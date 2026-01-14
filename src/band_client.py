import requests
import logging

class BandClient:
    BASE_URL = "https://openapi.band.us/v2"

    def __init__(self, access_token):
        self.access_token = access_token
        self.logger = logging.getLogger(__name__)

    def get_posts(self, band_key):
        """
        Fetches all posts from a specific band using the Naver Band API.
        """
        posts = []
        url = f"{self.BASE_URL}/band/posts"
        params = {
            "access_token": self.access_token,
            "band_key": band_key,
            "locale": "ko_KR"
        }

        self.logger.info(f"Starting to fetch posts for band_key: {band_key}")

        while True:
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("result_code") != 1:
                    self.logger.error(f"API Error: {data}")
                    break

                items = data.get("result_data", {}).get("items", [])
                if not items:
                    break

                posts.extend(items)
                self.logger.info(f"Fetched {len(items)} posts. Total so far: {len(posts)}")

                paging = data.get("result_data", {}).get("paging", {})
                next_params = paging.get("next_params")

                if not next_params:
                    break

                # Update params for next page (next_params usually contains after parameter)
                # Ensure access_token is still there if next_params doesn't include it
                if 'access_token' not in next_params:
                    next_params['access_token'] = self.access_token

                params = next_params

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error fetching posts: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                break

        self.logger.info(f"Finished fetching. Total posts: {len(posts)}")
        return posts
