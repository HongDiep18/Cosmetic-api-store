from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_account
from app.modules.reviews.constants import (
    FORBIDDEN_REVIEW_OWNER,
    REVIEW_ALREADY_EXISTS,
    REVIEW_NOT_FOUND,
    REVIEW_PURCHASE_REQUIRED,
)
from app.modules.reviews.schemas import ReviewCreate, ReviewOut, ReviewUpdate
from app.modules.reviews.controller import (
    create_review,
    delete_review,
    get_review,
    has_purchased_product,
    has_user_reviewed_product,
    list_product_reviews,
    update_review,
)
from app.modules.auth.model import Account


router = APIRouter()


# Route 1: Lấy danh sách review của một sản phẩm (Public)
@router.get("/products/{productId}/reviews")
async def list_product_reviews_endpoint(productId: str):
    from app.modules.auth.model import Account

    reviews = await list_product_reviews(productId)
    result = []
    for review in reviews:
        review_dict = ReviewOut.model_validate(
            review, from_attributes=True
        ).model_dump()
        # Populate UserName từ Account
        try:
            account = await Account.get(review.UserID)
            if account and account.profile:
                review_dict["UserName"] = account.profile.fullName
            else:
                review_dict["UserName"] = "Anonymous"
        except Exception:
            review_dict["UserName"] = "Anonymous"
        result.append(review_dict)
    return result


# Route 2: Tạo review mới (Customer)
@router.post(
    "/products/{productId}/reviews",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_review_endpoint(
    productId: str,
    data: ReviewCreate,
    current_account: Account = Depends(get_current_account),
):
    # Kiểm tra role phải là User
    if current_account.role != "User":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users can create reviews",
        )

    user_id = str(current_account.id)

    # Đã đánh giá trước đó?
    if await has_user_reviewed_product(user_id, productId):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=REVIEW_ALREADY_EXISTS
        )

    # Kiểm tra đã mua hàng (nâng cao): bắt buộc mua mới được review
    purchased = await has_purchased_product(user_id, productId)
    if not purchased:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=REVIEW_PURCHASE_REQUIRED
        )

    review = await create_review(user_id, productId, data)
    return ReviewOut.model_validate(review, from_attributes=True)


# Route 3: Cập nhật review (chủ sở hữu)
@router.patch("/reviews/{reviewId}", response_model=ReviewOut)
async def update_review_endpoint(
    reviewId: str,
    data: ReviewUpdate,
    current_account: Account = Depends(get_current_account),
):
    review = await get_review(reviewId)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=REVIEW_NOT_FOUND
        )
    if str(review.UserID) != str(current_account.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_REVIEW_OWNER
        )
    updated = await update_review(reviewId, data)
    return ReviewOut.model_validate(updated, from_attributes=True)  # type: ignore[arg-type]


# Route 4: Xoá review (chủ sở hữu hoặc admin)
@router.delete("/reviews/{reviewId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review_endpoint(
    reviewId: str,
    current_account: Account = Depends(get_current_account),
):
    review = await get_review(reviewId)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=REVIEW_NOT_FOUND
        )
    is_owner = str(review.UserID) == str(current_account.id)
    is_admin = current_account.role.lower() == "admin"
    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_REVIEW_OWNER
        )
    await delete_review(reviewId)
    return None
