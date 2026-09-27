# Update serializers/__init__.py
with open('apps/tenants/serializers/__init__.py', 'a', encoding='utf-8') as f:
    f.write("\nfrom .membership import TenantMemberSerializer\n")

# Update views/__init__.py
with open('apps/tenants/views/__init__.py', 'a', encoding='utf-8') as f:
    f.write("\nfrom .membership import TenantMemberViewSet\n")

# Update urls.py
with open('apps/tenants/urls.py', 'r', encoding='utf-8') as f:
    urls_content = f.read()

urls_content = urls_content.replace(
    "from .views import TenantViewSet",
    "from .views import TenantViewSet, TenantMemberViewSet"
)
urls_content = urls_content.replace(
    "router.register(r'tenants', TenantViewSet)",
    "router.register(r'tenants', TenantViewSet)\nrouter.register(r'memberships', TenantMemberViewSet)"
)

with open('apps/tenants/urls.py', 'w', encoding='utf-8') as f:
    f.write(urls_content)
