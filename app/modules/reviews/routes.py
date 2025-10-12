# from fastapi import APIRouter, Depends, HTTPException, status

# from app.core.deps import get_current_account
# from app.modules.reviews.constants import (
#     FORBIDDEN_REVIEW_OWNER,
#     REVIEW_ALREADY_EXISTS,
#     REVIEW_NOT_FOUND,
#     REVIEW_PURCHASE_REQUIRED,
# )
# from app.modules.reviews.schemas import ReviewCreate, ReviewOut, ReviewUpdate
# from app.modules.reviews.controller import (
#     create_review,
#     delete_review,
#     get_review,
#     has_purchased_product,
#     has_user_reviewed_product,
#     list_product_reviews,
#     update_review,
# )
# from app.modules.users.model import User


# router = APIRouter()


# # Route 1: Lấy danh sách review của một sản phẩm (Public)
# @router.get("/products/{productId}/reviews", response_model=list[ReviewOut])
# async def list_product_reviews_endpoint(productId: str):
#     reviews = await list_product_reviews(productId)
#     return [ReviewOut.model_validate(r, from_attributes=True) for r in reviews]


# # Route 2: Tạo review mới (Customer)
# @router.post(
#     "/products/{productId}/reviews",
#     response_model=ReviewOut,
#     status_code=status.HTTP_201_CREATED,
# )
# async def create_review_endpoint(
#     productId: str,
#     data: ReviewCreate,
#     current_user: User = Depends(get_current_account),
# ):
#     # Đã đánh giá trước đó?
#     if await has_user_reviewed_product(current_user.id, productId):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail=REVIEW_ALREADY_EXISTS
#         )

#     # Kiểm tra đã mua hàng (nâng cao): bắt buộc mua mới được review
#     purchased = await has_purchased_product(current_user.id, productId)
#     if not purchased:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail=REVIEW_PURCHASE_REQUIRED
#         )

#     review = await create_review(current_user.id, productId, data)
#     return ReviewOut.model_validate(review, from_attributes=True)


# # Route 3: Cập nhật review (chủ sở hữu)
# @router.patch("/reviews/{reviewId}", response_model=ReviewOut)
# async def update_review_endpoint(
#     reviewId: str,
#     data: ReviewUpdate,
#     current_user: User = Depends(get_current_account),
# ):
#     review = await get_review(reviewId)
#     if not review:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail=REVIEW_NOT_FOUND
#         )
#     if str(review.userId) != str(current_user.id):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_REVIEW_OWNER
#         )
#     updated = await update_review(reviewId, data)
#     return ReviewOut.model_validate(updated, from_attributes=True)  # type: ignore[arg-type]


# # Route 4: Xoá review (chủ sở hữu hoặc admin)
# @router.delete("/reviews/{reviewId}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_review_endpoint(
#     reviewId: str,
#     current_user: User = Depends(get_current_account),
# ):
#     review = await get_review(reviewId)
#     if not review:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail=REVIEW_NOT_FOUND
#         )
#     is_owner = str(review.userId) == str(current_user.id)
#     is_admin = current_user.role == "admin"
#     if not (is_owner or is_admin):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN_REVIEW_OWNER
#         )
#     await delete_review(reviewId)
#     return None
