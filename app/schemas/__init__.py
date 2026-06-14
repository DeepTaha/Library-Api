from app.schemas.book import BookBase, BookCreate, BookResponse, BookUpdate
from app.schemas.borrowing import BorrowRequest, BorrowingResponse, ExtendRequest, BulkReturnRequest, BulkReturnResponse, BulkReturnFailure
from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse, RegisterRequest, ForgotPasswordRequest, UserUpdate, AdminResetPasswordRequest, ResetPasswordRequest
from app.schemas.analytics import AnalyticsSummaryResponse, TopBook

__all__ = ["BookBase", "BookCreate", "BookResponse", "BorrowRequest", "BorrowingResponse", "AnalyticsSummaryResponse", "TopBook"]
