"""SheerID Student Verification Main Program"""
import re
import random
import logging
import httpx
from typing import Dict, Optional, Tuple

from . import config
from .name_generator import NameGenerator, generate_email, generate_birth_date
from .img_generator import generate_image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class SheerIDVerifier:
    """SheerID Student Identity Verifier"""

    def __init__(self, verification_id: Optional[str] = None):
        self.verification_id = verification_id
        # Default device fingerprint if no ID yet, will be updated if new ID created
        self.device_fingerprint = self._generate_device_fingerprint(self.verification_id or "default")
        self.http_client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Origin": "https://my.sheerid.com",
                "Referer": f"https://my.sheerid.com/verify/{config.PROGRAM_ID}/",
                "X-SheerID-Device-Fingerprint": self.device_fingerprint,
                "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-site",
                "Connection": "keep-alive",
            }
        )

    def create_verification(self) -> str:
        """Create a fresh verificationId for YouTube"""
        body = {
            "programId": config.PROGRAM_ID,
            "locale": "en-US",
        }
        data, status = self._sheerid_request(
            "POST", f"{config.SHEERID_BASE_URL}/rest/v2/verification/", body
        )
        if status != 200 or not isinstance(data, dict) or not data.get("verificationId"):
            raise Exception(f"Failed to create new YouTube verification (Status {status}): {data}")

        self.verification_id = data["verificationId"]
        self.device_fingerprint = self._generate_device_fingerprint(self.verification_id)
        # Update client headers with new fingerprint and referer
        self.http_client.headers["X-SheerID-Device-Fingerprint"] = self.device_fingerprint
        self.http_client.headers["Referer"] = f"https://my.sheerid.com/verify/{config.PROGRAM_ID}/?verificationId={self.verification_id}"
        
        logger.info(f"✅ Created fresh verificationId: {self.verification_id}")
        return self.verification_id

    def __del__(self):
        if hasattr(self, "http_client"):
            self.http_client.close()

    @staticmethod
    def _generate_device_fingerprint(seed: str) -> str:
        """Generate a random 32-character hex fingerprint seeded for consistency"""
        rng = random.Random(seed)
        chars = '0123456789abcdef'
        return ''.join(rng.choice(chars) for _ in range(32))

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL (placeholder)"""
        return url

    @staticmethod
    def parse_verification_id(url: str) -> Optional[str]:
        match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _sheerid_request(
        self, method: str, url: str, body: Optional[Dict] = None
    ) -> Tuple[Dict, int]:
        """Send SheerID API request"""
        headers = {
            "Content-Type": "application/json",
        }

        try:
            response = self.http_client.request(
                method=method, url=url, json=body, headers=headers
            )
            try:
                data = response.json()
            except Exception:
                data = response.text
            return data, response.status_code
        except Exception as e:
            logger.error(f"SheerID request failed: {e}")
            raise

    def get_verification_status(self) -> Dict:
        """Get current verification status"""
        data, status = self._sheerid_request(
            "GET", 
            f"{config.MY_SHEERID_URL}/rest/v2/verification/{self.verification_id}"
        )
        if status != 200:
             raise Exception(f"Failed to get status: {status}")
        return data

    def _upload_to_s3(self, upload_url: str, img_data: bytes) -> bool:
        """Upload PNG to S3"""
        try:
            headers = {"Content-Type": "image/png"}
            response = self.http_client.put(
                upload_url, content=img_data, headers=headers, timeout=60.0
            )
            return 200 <= response.status_code < 300
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return False

    def verify(
        self,
        first_name: str = None,
        last_name: str = None,
        email: str = None,
        birth_date: str = None,
        school_id: str = None,
    ) -> Dict:
        """Execute verification workflow, removed status polling to reduce latency"""
        try:
            current_step = "initial"

            # Check current status first
            if self.verification_id:
                try:
                    status_info = self.get_verification_status()
                    current_step_status = status_info.get("currentStep")
                    logger.info(f"Current session status: {current_step_status}")

                    if current_step_status == "success":
                         return {
                            "success": True, 
                            "message": "Verification already successful",
                            "verification_id": self.verification_id,
                            "redirect_url": status_info.get("redirectUrl"),
                            "status": status_info
                         }
                    elif current_step_status == "error":
                         logger.warning(f"Verification {self.verification_id} is in ERROR state. Creating NEW session...")
                         self.create_verification()
                         current_step = "initial"
                    else:
                        current_step = current_step_status
                except Exception as e:
                    logger.warning(f"Could not check status, creating fresh session: {e}")
                    self.create_verification()
                    current_step = "initial"
            else:
                logger.info("No verificationId provided, creating fresh session...")
                self.create_verification()
                current_step = "initial"

            # Generate student info with seeded randomness for consistency
            if not first_name or not last_name:
                name = NameGenerator.generate(seed=self.verification_id)
                first_name = name["first_name"]
                last_name = name["last_name"]

            school_id = school_id or config.DEFAULT_SCHOOL_ID
            school = config.SCHOOLS[school_id]

            if not email:
                email = generate_email(first_name, last_name, seed=self.verification_id)
            if not birth_date:
                birth_date = generate_birth_date(seed=self.verification_id)

            self.device_fingerprint = self._generate_device_fingerprint(self.verification_id)

            logger.info(f"Student Information: {first_name} {last_name}")
            logger.info(f"Email: {email}")
            logger.info(f"School: {school['name']}")
            logger.info(f"Birthday: {birth_date}")
            logger.info(f"Verification ID: {self.verification_id}")

            # Generate student ID PNG
            logger.info("Step 1/4: Generating student ID PNG...")
            img_data = generate_image(first_name, last_name, school_id)
            file_size = len(img_data)
            logger.info(f"✅ PNG Size: {file_size / 1024:.2f}KB")

            # Submit student info
            should_do_step_2 = current_step in ["initial", "collectStudentPersonalInfo", None]
            
            if should_do_step_2:
                import time
                logger.info("Step 2/4: Submitting student info (human delay)...")
                time.sleep(random.uniform(4.0, 7.5))
                step2_body = {
                    "firstName": first_name,
                    "lastName": last_name,
                    "birthDate": birth_date,
                    "email": email,
                    "phoneNumber": "",
                    "organization": {
                        "id": int(school_id),
                        "idExtended": school["idExtended"],
                        "name": school["name"],
                    },
                    "deviceFingerprintHash": self.device_fingerprint,
                    "locale": "en-US",
                    "metadata": {
                        "marketConsentValue": False,
                        "refererUrl": f"{config.MY_SHEERID_URL}/verify/{config.PROGRAM_ID}/?verificationId={self.verification_id}",
                        "verificationId": self.verification_id,
                        "submissionOptIn": "By submitting the personal information above, I acknowledge that my personal information is being collected under the privacy policy of the business from which I am seeking a discount",
                    },
                }

                step2_data, step2_status = self._sheerid_request(
                    "POST",
                    f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/collectStudentPersonalInfo",
                    step2_body,
                )

                if step2_status != 200:
                    raise Exception(f"Step 2 failed (Status {step2_status}): {step2_data}")
                if step2_data.get("currentStep") == "error":
                    error_msg = ", ".join(step2_data.get("errorIds", ["Unknown error"]))
                    raise Exception(f"Step 2 error: {error_msg}")

                logger.info(f"✅ Step 2 complete: {step2_data.get('currentStep')}")
                current_step = step2_data.get("currentStep", current_step)
            else:
                 logger.info(f"Skipping Step 2 (Current Status: {current_step})")

            # Skip SSO if needed
            if current_step in ["sso", "collectStudentPersonalInfo"]:
                logger.info("Step 3/4: Skipping SSO verification...")
                step3_data, _ = self._sheerid_request(
                    "DELETE",
                    f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/sso",
                )
                logger.info(f"✅ Step 3 complete: {step3_data.get('currentStep')}")
                current_step = step3_data.get("currentStep", current_step)

            # Upload document and complete submission
            logger.info("Step 4/4: Requesting and uploading document...")
            step4_body = {
                "files": [
                    {"fileName": "student_card.png", "mimeType": "image/png", "fileSize": file_size}
                ]
            }
            step4_data, step4_status = self._sheerid_request(
                "POST",
                f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/docUpload",
                step4_body,
            )
            if not step4_data.get("documents"):
                raise Exception("Failed to get upload URL")

            upload_url = step4_data["documents"][0]["uploadUrl"]
            logger.info("✅ Successfully obtained upload URL")
            if not self._upload_to_s3(upload_url, img_data):
                raise Exception("S3 upload failed")
            logger.info("✅ Student ID uploaded successfully")

            step6_data, _ = self._sheerid_request(
                "POST",
                f"{config.SHEERID_BASE_URL}/rest/v2/verification/{self.verification_id}/step/completeDocUpload",
            )
            logger.info(f"✅ Document submission complete: {step6_data.get('currentStep')}")
            final_status = step6_data

            # No status polling, just return and wait for review
            return {
                "success": True,
                "pending": True,
                "message": "Document submitted, waiting for review",
                "verification_id": self.verification_id,
                "redirect_url": final_status.get("redirectUrl"),
                "status": final_status,
            }

        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return {"success": False, "message": str(e), "verification_id": self.verification_id}


def main():
    """Main Function - Command Line Interface"""
    import sys

    print("=" * 60)
    print("SheerID Student Identity Verification Tool (Python Version)")
    print("=" * 60)
    print()

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Please enter SheerID Verification URL: ").strip()

    if not url:
        print("❌ Error: No URL provided")
        sys.exit(1)

    verification_id = SheerIDVerifier.parse_verification_id(url)
    if not verification_id:
        print("❌ Error: Invalid verification ID format")
        sys.exit(1)

    print(f"✅ Parsed Verification ID: {verification_id}")
    print()

    verifier = SheerIDVerifier(verification_id)
    result = verifier.verify()

    print()
    print("=" * 60)
    print("Verification Results:")
    print("=" * 60)
    print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
    print(f"Message: {result['message']}")
    if result.get("redirect_url"):
        print(f"Redirect URL: {result['redirect_url']}")
    print("=" * 60)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit(main())
