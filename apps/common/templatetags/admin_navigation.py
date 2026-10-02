from django import template

register = template.Library()


@register.simple_tag
def admin_sections(app_list):
    grouped = {
        "Business": [],
        "Garments & Designs": [],
        "Measurements": [],
        "Materials": [],
        "Users & Access": [],
        "System": [],
    }
    for app in app_list:
        app_label = app.get("app_label")
        for model in app.get("models", []):
            object_name = model.get("object_name")
            if app_label == "clients":
                section = "Business"
            elif app_label == "tenants":
                if object_name in {"TenantMember", "MembershipWorkFunction"}:
                    section = "Users & Access"
                elif object_name == "Tenant":
                    section = "Business"
                else:
                    section = "System"
            elif app_label == "accounts":
                section = "Users & Access"
            elif app_label == "catalog":
                if object_name.startswith("Measurement"):
                    section = "Measurements"
                elif object_name == "Material":
                    section = "Materials"
                else:
                    section = "Garments & Designs"
            else:
                section = "System"
            grouped[section].append(model)
    return [
        {"name": name, "models": models} for name, models in grouped.items() if models
    ]
