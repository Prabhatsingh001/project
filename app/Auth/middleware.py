import logging
import time

logger = logging.getLogger('api_logger')

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time
        user = getattr(request, 'user', None)
        username = user.username if user and user.is_authenticated else 'Anonymous'

        logger.info(
            f'{request.method} {request.get_full_path()} '
            f'Status: {response.status_code} '
            f'User: {username} '
            f'Duration: {duration:.3f}s'
        )
        return response
