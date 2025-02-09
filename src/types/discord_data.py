from src.types.TypeClass import TypeClass

class ReviewScore(TypeClass):
    def __init__(self):
        self.total_reviews: int = None
        self.review_score_percentage: float = None
        self.review_total_positive: int = None
        self.review_total_negative: int = None
        self.review_score_description: str = None