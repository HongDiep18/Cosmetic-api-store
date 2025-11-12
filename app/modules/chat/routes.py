from __future__ import annotations
import unicodedata
from typing import List, Optional, Dict, Any
import traceback

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.config import settings
from app.modules.products.model import Product

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    from groq import Groq
except Exception:
    Groq = None


router = APIRouter()

# Groq models to try (free, no quota)
GROQ_MODEL_CANDIDATES = [
    "mixtral-8x7b-32768",
    "llama-2-70b-chat",
    "gemma-7b-it",
]

# Keep Gemini disabled if models are unavailable; fallbacks will handle responses.
# Initial candidates to try (older name + common Generative AI model ids)
GENAI_MODEL_CANDIDATES = [
    "gemini-1.5-flash",
    "models/text-bison-001",
    "models/chat-bison-001",
]


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
    topK: int = 5


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _tokenize_query(query: str) -> List[str]:
    tokens = [t.strip().lower() for t in query.split() if len(t.strip()) > 1]
    normalized_tokens = []
    for token in tokens:
        normalized_tokens.append(token)
        accentless = _strip_accents(token)
        if accentless != token:
            normalized_tokens.append(accentless)
    # keep unique while preserving order
    seen = set()
    deduped = []
    for tok in normalized_tokens:
        if tok not in seen:
            seen.add(tok)
            deduped.append(tok)
    return deduped[:8]


def _build_context_snippets(docs: List[Product]) -> str:
    lines: List[str] = []
    for p in docs[:10]:
        try:
            desc = (getattr(p, "description", "") or "")[:160]
            product_name = getattr(p, "productName", "N/A")
            brand_name = getattr(p, "brand", {}).get("name", "N/A") if hasattr(p, "brand") and isinstance(getattr(p, "brand", None), dict) else (getattr(p, "brand", None) or "N/A")
            price = getattr(p, "price", 0)
            stock = getattr(p, "stock", 0)
            category_name = getattr(p, "category", {}).get("name", "N/A") if hasattr(p, "category") and isinstance(getattr(p, "category", None), dict) else "N/A"
            rating = getattr(p, "rating", 0) or 0
            lines.append(
                f"- {product_name} | Brand: {brand_name} | Price: {price} VNĐ | Stock: {stock} | Category: {category_name} | Rating: {rating}/5 | Mô tả: {desc}..."
            )
        except Exception:
            continue
    return "\n".join(lines) if lines else "Không tìm thấy sản phẩm liên quan."


def _score_products(query_tokens: List[str], products: List[Product]) -> List[Product]:
    if not products or not query_tokens:
        return products

    scored: List[tuple[float, Product]] = []
    for p in products:
        brand_name = ""
        category_name = ""
        if hasattr(p, "brand") and isinstance(getattr(p, "brand", None), dict):
            brand_name = getattr(p, "brand", {}).get("name", "")
        if hasattr(p, "category") and isinstance(getattr(p, "category", None), dict):
            category_name = getattr(p, "category", {}).get("name", "")
        
        haystack_raw = " ".join(
            filter(
                None,
                [
                    getattr(p, "productName", ""),
                    getattr(p, "description", ""),
                    brand_name,
                    category_name,
                ],
            )
        )
        haystack_norm = _strip_accents(haystack_raw.lower())
        score = 0.0
        for tok in query_tokens:
            tok_norm = _strip_accents(tok.lower())
            if tok_norm and tok_norm in haystack_norm:
                score += 1.0
        # Add slight boost for rating/review
        rating = getattr(p, "rating", 0) or 0
        review_count = getattr(p, "reviewCount", 0) or 0
        score += (rating or 0) * 0.05
        score += min(review_count, 1000) / 2000.0
        if score > 0:
            scored.append((score, p))

    # Sort by score desc
    scored.sort(key=lambda item: item[0], reverse=True)
    return [p for _, p in scored]


def _summarize_products(
    docs: List[Product], query_tokens: List[str], matched: bool
) -> str:
    if not docs:
        if query_tokens:
            search_hint = ", ".join(query_tokens[:3])
            return (
                f"Xin lỗi, tôi chưa tìm thấy sản phẩm liên quan tới: {search_hint}. "
                "Bạn có thể cung cấp chi tiết hơn (tên đầy đủ, công dụng, thương hiệu) để tôi hỗ trợ chính xác hơn."
            )
        return "Xin lỗi, tôi chưa tìm thấy sản phẩm phù hợp. Bạn có thể mô tả rõ hơn về nhu cầu hoặc tên sản phẩm nhé."

    top_docs = docs[:3]
    bullets = []
    for idx, product in enumerate(top_docs, start=1):
        product_name = getattr(product, "productName", "Không rõ")
        brand_name = "Chưa cập nhật"
        if hasattr(product, "brand") and isinstance(getattr(product, "brand", None), dict):
            brand_name = getattr(product, "brand", {}).get("name", "Chưa cập nhật")
        parts = [f"{idx}. {product_name} ({brand_name})"]
        price = getattr(product, "price", None)
        if price not in (None, ""):
            parts.append(f"Giá: ~{price} VNĐ")
        stock = getattr(product, "stock", None)
        if isinstance(stock, (int, float)):
            parts.append(f"Tồn kho: {int(stock)}")
        rating = getattr(product, "rating", None)
        if rating not in (None, ""):
            parts.append(f"Đánh giá: {rating}/5")
        category = None
        if hasattr(product, "category") and isinstance(getattr(product, "category", None), dict):
            category = getattr(product, "category", {}).get("name", None)
        if category:
            parts.append(f"Danh mục: {category}")
        bullets.append(" - " + " | ".join(parts))

    intro = "Dưới đây là những sản phẩm nổi bật bạn có thể tham khảo:"
    if matched and query_tokens:
        intro = f"Dựa trên từ khóa {', '.join(query_tokens[:3])}, tôi đề xuất:"
    elif query_tokens:
        intro = (
            f"Chưa tìm thấy sản phẩm khớp trực tiếp với từ khóa {', '.join(query_tokens[:3])}. "
            "Tuy nhiên bạn có thể cân nhắc các lựa chọn bán chạy sau:"
        )

    closing = "Bạn muốn biết thêm chi tiết sản phẩm nào hoặc cần gợi ý khác không?"

    return "\n".join([intro, *bullets, closing])


def _response_from_docs(
    docs: List[Product], query_tokens: List[str], matched: bool
) -> Dict[str, Any]:
    summary = _summarize_products(docs, query_tokens, matched)
    return {
        "reply": summary,
        "contextUsed": bool(docs),
        "matches": [
            {
                "id": str(getattr(p, "id", "")),
                "name": getattr(p, "productName", ""),
                "price": getattr(p, "price", 0),
                "brand": getattr(p, "brand", {}).get("name", "") if hasattr(p, "brand") and isinstance(getattr(p, "brand", None), dict) else "",
                "image": getattr(p, "image", ""),
            }
            for p in docs
        ],
    }


@router.post("/chat")
async def chat_endpoint(req: ChatRequest) -> Dict[str, Any]:
    try:
        # Validate message
        query = (req.message or "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Message is required")

        print(f"💬 Chat request: {query[:100]}")

        tokens = _tokenize_query(query)

        # Build search filters using regex over key fields
        docs: List[Product] = []
        matched_results = False
        try:
            mongo_filters: List[Dict[str, Any]] = []
            for token in tokens:
                regex = {"$regex": token, "$options": "i"}
                mongo_filters.extend(
                    [
                        {"productName": regex},
                        {"description": regex},
                        {"brand.name": regex},
                        {"category.name": regex},
                    ]
                )

            if mongo_filters:
                docs = (
                    await Product.find({"$or": mongo_filters})
                    .sort("-rating", "-reviewCount")
                    .limit(req.topK)
                    .to_list()
                )
                print(f"✅ Found {len(docs)} products with filters")
                matched_results = len(docs) > 0

            # Fallback: get top rated products when nothing matches
            if not docs:
                docs = (
                    await Product.find_all().sort("-rating").limit(req.topK).to_list()
                )
                print(f"✅ Using fallback: {len(docs)} products")
        except Exception as search_err:
            print(f"❌ Search error: {search_err}")
            traceback.print_exc()
            # Continue with empty docs instead of failing
            docs = []

        # If regex search was weak, apply local scoring
        if len(tokens) > 0:
            try:
                candidate_count = max(req.topK * 5, 20)
                candidates = await Product.find_all().limit(candidate_count).to_list()
                scored = _score_products(tokens, candidates)
                if scored:
                    docs = scored[: req.topK]
                    print(f"✅ Rescored products count: {len(docs)}")
                    matched_results = True
            except Exception as scoring_err:
                print(f"❌ Scoring error: {scoring_err}")
                traceback.print_exc()

        # Prepare summary for fallback/augmentation
        context = _build_context_snippets(docs)
        summary_response = _response_from_docs(docs, tokens, matched_results)

        # Try Groq first (free, no quota limit)
        if settings.GROQ_API_KEY and Groq is not None:
            try:
                print("ℹ️ Using Groq API for chat generation...")
                groq_client = Groq(api_key=settings.GROQ_API_KEY)

                system_msg = (
                    "Bạn là trợ lý AI thông minh cho cửa hàng mỹ phẩm trực tuyến. "
                    "Nhiệm vụ của bạn là trả lời câu hỏi của khách hàng về sản phẩm, giá cả, thương hiệu, tồn kho một cách thân thiện và chính xác. "
                    "Luôn trả lời bằng tiếng Việt. Ưu tiên sử dụng thông tin từ Context được cung cấp. "
                    "Nếu không có thông tin trong Context, hãy nói rõ bạn không biết thay vì bịa đặt."
                )

                user_content = (
                    f"=== THÔNG TIN SẢN PHẨM TỪ CƠ SỞ DỮ LIỆU ===\n{context}\n\n"
                    f"=== CÂU HỎI CỦA KHÁCH HÀNG ===\n{req.message}\n\n"
                    f"=== HƯỚNG DẪN ===\n"
                    f"- Trả lời ngắn gọn, thân thiện, chính xác bằng tiếng Việt.\n"
                    f"- Ưu tiên thông tin từ Context trên.\n"
                    f"- Nếu không có thông tin, hãy nói rõ bạn không biết.\n"
                    f"- Không bịa đặt giá, tồn kho, hoặc thông tin không có trong Context.\n"
                )

                messages = [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_content},
                ]

                for groq_model in GROQ_MODEL_CANDIDATES:
                    try:
                        print(f"ℹ️ Trying Groq model: {groq_model}")
                        response = groq_client.chat.completions.create(
                            model=groq_model,
                            messages=messages,
                            temperature=0.7,
                            max_tokens=1024,
                        )

                        text = response.choices[0].message.content.strip()
                        if text:
                            print(
                                f"✅ Generated response using Groq {groq_model}: {text[:100]}..."
                            )
                            return {
                                "reply": text,
                                "contextUsed": bool(docs),
                                "matches": summary_response["matches"],
                            }
                    except Exception as groq_err:
                        print(f"❌ Groq error with {groq_model}: {groq_err}")
                        continue
            except Exception as groq_init_err:
                print(f"❌ Groq initialization error: {groq_init_err}")

        # If Gemini is not available, return summary directly
        if not settings.GEMINI_API_KEY or genai is None:
            if not settings.GEMINI_API_KEY:
                print("❌ Gemini API key not configured. Using summary fallback.")
            if genai is None:
                print("❌ google-generativeai not installed. Using summary fallback.")
            return summary_response

        # Configure Gemini
        genai.configure(api_key=settings.GEMINI_API_KEY)
        system_preamble = (
            "Bạn là trợ lý AI thông minh cho cửa hàng mỹ phẩm trực tuyến. "
            "Nhiệm vụ của bạn là trả lời câu hỏi của khách hàng về sản phẩm, giá cả, thương hiệu, tồn kho một cách thân thiện và chính xác. "
            "Luôn trả lời bằng tiếng Việt. Ưu tiên sử dụng thông tin từ Context được cung cấp. "
            "Nếu không có thông tin trong Context, hãy nói rõ bạn không biết thay vì bịa đặt."
        )

        history_text = ""
        if req.history:
            for m in req.history[-6:]:
                if m.role != "system":
                    history_text += f"\n[{m.role}]: {m.content}"

        final_prompt = (
            f"{system_preamble}\n\n"
            f"=== THÔNG TIN SẢN PHẨM TỪ CƠ SỞ DỮ LIỆU ===\n{context}\n\n"
            f"=== LỊCH SỬ CUỘC TRÒ CHUYỆN ===\n{history_text if history_text else 'Chưa có lịch sử'}\n\n"
            f"=== CÂU HỎI CỦA KHÁCH HÀNG ===\n{req.message}\n\n"
            f"=== HƯỚNG DẪN ===\n"
            f"- Trả lời ngắn gọn, thân thiện, chính xác bằng tiếng Việt.\n"
            f"- Ưu tiên thông tin từ Context trên.\n"
            f"- Nếu không có thông tin, hãy nói rõ bạn không biết.\n"
            f"- Không bịa đặt giá, tồn kho, hoặc thông tin không có trong Context.\n"
        )

        model_errors: List[str] = []
        for model_name in GENAI_MODEL_CANDIDATES:
            try:
                model = genai.GenerativeModel(model_name)
                result = model.generate_content(final_prompt)
                text = (getattr(result, "text", "") or "").strip()

                if not text and hasattr(result, "candidates"):
                    for candidate in getattr(result, "candidates", []):
                        try:
                            content = getattr(candidate, "content", None)
                            if content and hasattr(content, "parts"):
                                parts = content.parts
                                maybe_text = " ".join(
                                    [p.text for p in parts if hasattr(p, "text")]
                                )
                                if maybe_text.strip():
                                    text = maybe_text.strip()
                                    break
                        except Exception:
                            continue

                if not text:
                    print(
                        f"⚠️ Gemini model {model_name} returned empty text. Trying next model."
                    )
                    continue

                print(f"✅ Generated response using {model_name}: {text[:100]}...")
                return {
                    "reply": text,
                    "contextUsed": bool(docs),
                    "matches": summary_response["matches"],
                }
            except Exception as gemini_err:
                err_msg = f"{model_name}: {gemini_err}"
                model_errors.append(err_msg)
                print(f"❌ Gemini error with {model_name}: {gemini_err}")
                # Avoid noisy stack traces for expected 404 errors
                if "404" not in str(gemini_err):
                    traceback.print_exc()

        # All Gemini models failed; return summary
        # All initial Gemini candidates failed; try to list available models
        if model_errors:
            print("🤖 Initial Gemini attempts failed:")
            for err in model_errors:
                print(f"   - {err}")

        # As a fallback, try to query the GenAI SDK for available models and
        # attempt generation with any sensible candidates found. This helps
        # in environments where model names or APIs changed (e.g. gemini-* -> models/*).
        if genai and hasattr(genai, "list_models"):
            try:
                print("ℹ️ Querying available GenAI models...")
                available = genai.list_models()
                candidate_names: List[str] = []
                for m in available:
                    name = None
                    try:
                        name = getattr(m, "name", None)
                    except Exception:
                        try:
                            name = m.get("name")
                        except Exception:
                            name = None
                    if name:
                        candidate_names.append(name)

                print(f"ℹ️ Found {len(candidate_names)} models. Trying best matches...")

                # Heuristic filter: prefer models with common generation identifiers
                heuristics = ("bison", "gemini", "chat", "text", "model")
                filtered = [
                    n
                    for n in candidate_names
                    if any(h in n.lower() for h in heuristics)
                ]

                for candidate in filtered:
                    try:
                        print(f"ℹ️ Trying dynamic model: {candidate}")
                        model = genai.GenerativeModel(candidate)
                        result = model.generate_content(final_prompt)
                        text = (getattr(result, "text", "") or "").strip()

                        if not text and hasattr(result, "candidates"):
                            for cand in getattr(result, "candidates", []):
                                try:
                                    content = getattr(cand, "content", None)
                                    if content and hasattr(content, "parts"):
                                        parts = content.parts
                                        maybe_text = " ".join(
                                            [
                                                p.text
                                                for p in parts
                                                if hasattr(p, "text")
                                            ]
                                        )
                                        if maybe_text.strip():
                                            text = maybe_text.strip()
                                            break
                                except Exception:
                                    continue

                        if text:
                            print(
                                f"✅ Generated response using {candidate}: {text[:100]}..."
                            )
                            return {
                                "reply": text,
                                "contextUsed": bool(docs),
                                "matches": summary_response["matches"],
                            }
                    except Exception as dyn_err:
                        print(f"❌ Error using dynamic model {candidate}: {dyn_err}")
                        continue
            except Exception as list_err:
                print(f"❌ Could not list GenAI models: {list_err}")

        # Final fallback: return summary
        print("🤖 Using summary fallback due to Gemini/model issues.")
        return summary_response
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unexpected error in chat_endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
