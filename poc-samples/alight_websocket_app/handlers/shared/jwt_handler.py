"""
JWT Token Handler module for decoding and reading JWT tokens.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt


class JWTDecoder:
    """
    A class to handle JWT token decoding and content reading operations.
    """

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize the JWTDecoder.

        Args:
            secret_key (Optional[str]): The secret key used for verifying tokens.
                                      If None, tokens will be decoded without verification.
        """
        self.secret_key = secret_key

    def decode_token(self, token: str, verify: bool = True) -> Dict[str, Any]:
        """
        Decode a JWT token and return its contents.

        Args:
            token (str): The JWT token to decode
            verify (bool): Whether to verify the token signature. Defaults to True.
                         If True, requires secret_key to be set.

        Returns:
            Dict[str, Any]: The decoded token contents

        Raises:
            jwt.InvalidTokenError: If the token is invalid
            jwt.ExpiredSignatureError: If the token has expired
            ValueError: If verify=True but no secret_key was provided
        """
        try:
            if verify and not self.secret_key:
                raise ValueError("Secret key is required for token verification")

            options = {
                "verify_signature": verify,
                "verify_exp": verify,
                "verify_iat": verify,
            }

            decoded = jwt.decode(
                token,
                self.secret_key if verify else None,
                algorithms=["HS256"] if verify else None,
                options=options,
            )
            return decoded

        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")

    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Get the expiration time from a token.

        Args:
            token (str): The JWT token

        Returns:
            Optional[datetime]: The expiration datetime if present, None otherwise
        """
        try:
            decoded = self.decode_token(token, verify=False)
            exp_timestamp = decoded.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp)
            return None
        except jwt.InvalidTokenError:
            return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if a token has expired.

        Args:
            token (str): The JWT token

        Returns:
            bool: True if the token has expired, False otherwise
        """
        try:
            expiry = self.get_token_expiry(token)
            if expiry is None:
                return False
            return datetime.now() > expiry
        except jwt.InvalidTokenError:
            return True

    def get_token_claims(self, token: str, verify: bool = True) -> Dict[str, Any]:
        """
        Get all claims from a token.

        Args:
            token (str): The JWT token
            verify (bool): Whether to verify the token signature

        Returns:
            Dict[str, Any]: Dictionary containing all token claims
        """
        return self.decode_token(token, verify=verify)

    # generate sample jwt token
    def generate_sample_token(self) -> str:
        """
        Generate a sample JWT token for demonstration purposes.
        Includes standard JWT claims and custom application claims.

        Returns:
            str: A sample JWT token with various claims
        """
        current_time = datetime.utcnow()
        payload = {
            # Standard JWT Claims
            "sub": "1234567890",  # Subject
            "iss": "https://api.example.com",  # Issuer
            "aud": "example_client_id",  # Audience
            "iat": current_time,  # Issued At
            "exp": current_time + timedelta(days=1),  # Expiration Time
            "nbf": current_time,  # Not Before
            "jti": "unique-jwt-id-123",  # JWT ID
            # Custom Claims
            "name": "Leslie Daniel Raj",
            "email": "john.doe@example.com",
            "roles": ["user", "admin"],
            "permissions": ["read", "write", "delete"],
            "org_id": "org_123456",
            "user_metadata": {
                "first_name": "John",
                "last_name": "Doe",
                "country": "US",
                "verified": True,
            },
        }
        return jwt.encode(payload, "secret", algorithm="HS256")
