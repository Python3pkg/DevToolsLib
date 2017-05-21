from django.conf import settings

def print_settings():
    for k, v in list(settings._wrapped.__dict__.items()):
        print(k, '||', v)
        
print_settings()