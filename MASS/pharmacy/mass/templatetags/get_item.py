from django import template

register = template.Library()

@register.filter
def get_item(value, index):
    #Zwraca element z listy na podstawie indeksu
    try:
        return value[index]
    except IndexError:
        return None  # lub domyślna wartość, jeśli indeks jest poza zakresem
