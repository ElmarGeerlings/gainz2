from django.template.loader import render_to_string

def render_toast(message, variant="success"):
    return render_to_string(
        "components/toast.html",
        {
            "message": message,
            "variant": variant,
        },
    )
