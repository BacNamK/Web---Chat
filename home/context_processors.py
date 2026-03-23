from blog.models import blog
from .models import Report


def admin_badges(request):
    # Counts used in the admin section of the navbar.
    return {
        "not_verify": blog.objects.filter(verify=False).count(),
        "report_count": Report.objects.count(),
    }
