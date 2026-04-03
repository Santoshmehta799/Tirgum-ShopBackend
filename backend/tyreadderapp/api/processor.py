from django.db.models import F, Func

def get_optimized_value(value):
    return Func(
        F(value), 
        function='REPLACE',
        template="LOWER(REPLACE(REPLACE(%(expressions)s, ' ', ''), '-', ''))"
    )