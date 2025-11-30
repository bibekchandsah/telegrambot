"""User profile management service."""
import json
from typing import Optional, Dict
from src.db.redis_client import RedisClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class UserProfile:
    """User profile data class."""
    
    def __init__(self, user_id: int, nickname: str, gender: str, country: str):
        self.user_id = user_id
        self.nickname = nickname
        self.gender = gender
        self.country = country
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "gender": self.gender,
            "country": self.country,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "UserProfile":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            nickname=data["nickname"],
            gender=data["gender"],
            country=data["country"],
        )
    
    def to_display(self) -> str:
        """Format profile for display."""
        gender_emoji = {
            "Male": "👨",
            "Female": "👩",
            "Other": "🧑",
        }
        
        return (
            f"👤 **Profile**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📝 Nickname: {self.nickname}\n"
            f"{gender_emoji.get(self.gender, '🧑')} Gender: {self.gender}\n"
            f"🌍 Country: {self.country}"
        )


class ProfileManager:
    """Manages user profiles."""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def create_profile(
        self, 
        user_id: int, 
        nickname: str, 
        gender: str, 
        country: str
    ) -> UserProfile:
        """
        Create or update user profile.
        
        Args:
            user_id: Telegram user ID
            nickname: User's chosen nickname
            gender: User's gender
            country: User's country
            
        Returns:
            Created UserProfile object
        """
        try:
            profile = UserProfile(user_id, nickname, gender, country)
            profile_key = f"profile:{user_id}"
            
            # Store as JSON string in Redis
            await self.redis.set(
                profile_key,
                json.dumps(profile.to_dict()),
                ex=None,  # No expiry - profiles are permanent until deleted
            )
            
            logger.info(
                "profile_created",
                user_id=user_id,
                nickname=nickname,
                gender=gender,
                country=country,
            )
            
            return profile
            
        except Exception as e:
            logger.error(
                "profile_creation_error",
                user_id=user_id,
                error=str(e),
            )
            raise
    
    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """
        Get user profile.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            UserProfile if exists, None otherwise
        """
        try:
            profile_key = f"profile:{user_id}"
            data = await self.redis.get(profile_key)
            
            if not data:
                return None
            
            profile_dict = json.loads(data.decode())
            return UserProfile.from_dict(profile_dict)
            
        except Exception as e:
            logger.error(
                "profile_get_error",
                user_id=user_id,
                error=str(e),
            )
            return None
    
    async def update_profile(
        self,
        user_id: int,
        nickname: Optional[str] = None,
        gender: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Optional[UserProfile]:
        """
        Update user profile fields.
        
        Args:
            user_id: Telegram user ID
            nickname: New nickname (optional)
            gender: New gender (optional)
            country: New country (optional)
            
        Returns:
            Updated UserProfile if exists, None otherwise
        """
        try:
            # Get existing profile
            profile = await self.get_profile(user_id)
            if not profile:
                return None
            
            # Update fields
            if nickname:
                profile.nickname = nickname
            if gender:
                profile.gender = gender
            if country:
                profile.country = country
            
            # Save updated profile
            await self.create_profile(
                user_id,
                profile.nickname,
                profile.gender,
                profile.country,
            )
            
            logger.info(
                "profile_updated",
                user_id=user_id,
                updated_fields={
                    "nickname": nickname is not None,
                    "gender": gender is not None,
                    "country": country is not None,
                }
            )
            
            return profile
            
        except Exception as e:
            logger.error(
                "profile_update_error",
                user_id=user_id,
                error=str(e),
            )
            raise
    
    async def delete_profile(self, user_id: int) -> bool:
        """
        Delete user profile.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if deleted, False if didn't exist
        """
        try:
            profile_key = f"profile:{user_id}"
            deleted = await self.redis.delete(profile_key)
            
            if deleted:
                logger.info("profile_deleted", user_id=user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                "profile_delete_error",
                user_id=user_id,
                error=str(e),
            )
            raise
    
    async def has_profile(self, user_id: int) -> bool:
        """
        Check if user has a profile.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if profile exists, False otherwise
        """
        try:
            profile_key = f"profile:{user_id}"
            return await self.redis.exists(profile_key)
        except Exception as e:
            logger.error(
                "profile_exists_check_error",
                user_id=user_id,
                error=str(e),
            )
            return False


# Common countries list
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia",
    "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
    "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina",
    "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cambodia",
    "Cameroon", "Canada", "Cape Verde", "Central African Republic", "Chad", "Chile", "China",
    "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador", "Egypt",
    "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland",
    "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada",
    "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy",
    "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "North Korea", "South Korea",
    "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
    "Liechtenstein", "Lithuania", "Luxembourg", "Macedonia", "Madagascar", "Malawi", "Malaysia",
    "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico",
    "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique",
    "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua",
    "Niger", "Nigeria", "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama",
    "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar",
    "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
    "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
    "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands",
    "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname",
    "Swaziland", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
    "Thailand", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan",
    "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
    "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen",
    "Zambia", "Zimbabwe", "Other"
]

# Gender options
GENDERS = ["Male", "Female", "Other"]


def validate_nickname(nickname: str) -> tuple[bool, str]:
    """
    Validate nickname.
    
    Returns:
        (is_valid, error_message)
    """
    if not nickname:
        return False, "Nickname cannot be empty"
    
    if len(nickname) < 2:
        return False, "Nickname must be at least 2 characters"
    
    if len(nickname) > 30:
        return False, "Nickname must be less than 30 characters"
    
    # Allow letters, numbers, spaces, underscores, hyphens
    if not all(c.isalnum() or c in " _-" for c in nickname):
        return False, "Nickname can only contain letters, numbers, spaces, underscores, and hyphens"
    
    return True, ""


def validate_gender(gender: str) -> tuple[bool, str]:
    """
    Validate gender.
    
    Returns:
        (is_valid, error_message)
    """
    if gender not in GENDERS:
        return False, f"Gender must be one of: {', '.join(GENDERS)}"
    
    return True, ""


def validate_country(country: str) -> tuple[bool, str]:
    """
    Validate country.
    
    Returns:
        (is_valid, error_message)
    """
    if country not in COUNTRIES:
        return False, "Please select a valid country from the list"
    
    return True, ""
