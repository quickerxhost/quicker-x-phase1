from rest_framework.pagination import PageNumberPagination

from apps.core.responses import success_response


class StandardResultsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return success_response(
            data=data,
            message="Success",
            extra_meta={
                "pagination": {
                    "count": self.page.paginator.count,
                    "page": self.page.number,
                    "total_pages": self.page.paginator.num_pages,
                    "page_size": self.get_page_size(self.request),
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                }
            },
        )
