from rest_framework.pagination import PageNumberPagination


class LmsPagination(PageNumberPagination):
    page_size = 5                    # элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # ?page_size=10
    max_page_size = 50               # больше 50 запросить нельзя