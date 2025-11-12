from __future__ import annotations
from typing import List, Optional

from app.modules.orders.model import Order
from app.modules.reviews.model import Review
from app.modules.reviews.schemas import ReviewCreate, ReviewUpdate


async def list_product_reviews(productId: str) -> List[Review]:
    return await Review.find(Review.ProductID == productId).sort("-CreatedAt").to_list()


async def has_purchased_product(userId: str, productId: str) -> bool:
    orders = await Order.find(Order.UserID == userId).to_list()
    for order in orders:
        for item in order.Items:
            if str(item.ProductID) == productId:
                return True
    return False


async def has_user_reviewed_product(userId: str, productId: str) -> bool:
    existing = await Review.find_one(
        (Review.UserID == userId) & (Review.ProductID == productId)
    )
    return existing is not None


async def create_review(userId: str, productId: str, data: ReviewCreate) -> Review:
    review = Review(
        UserID=userId,
        ProductID=productId,
        Rating=data.Rating,
        Comment=data.Comment,
    )
    await review.insert()
    return review


async def get_review(review_id: str) -> Optional[Review]:
    return await Review.get(review_id)


async def update_review(review_id: str, data: ReviewUpdate) -> Optional[Review]:
    review = await Review.get(review_id)
    if not review:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(review, key, value)
    await review.save()
    return review


async def delete_review(review_id: str) -> bool:
    review = await Review.get(review_id)
    if not review:
        return False
    await review.delete()
    return True
