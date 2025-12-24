from django.conf import settings

def default_tracking_ids(request):
    return {
        'DEFAULT_GA_ID': getattr(settings, 'DEFAULT_GA_ID', 'G-GE353FP9KK'),
        'DEFAULT_GTM_ID': getattr(settings, 'DEFAULT_GTM_ID', 'GTM-TMHQ84N'),
    }