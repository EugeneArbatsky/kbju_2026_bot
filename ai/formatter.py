"""
Форматирование данных для вывода
"""

def format_dish(dish: dict, index: int = None) -> str:
    """Форматирует одно блюдо для вывода"""
    name = dish['name']
    calories = dish['calories']
    protein = dish['protein']
    fat = dish['fat']
    carbs = dish['carbs']
    
    if index is not None:
        return f"{index}. {name}\n{calories} ккал, {protein} белков, {fat} жиров, {carbs} углеводов"
    else:
        return f"{name}\n{calories} ккал, {protein} белков, {fat} жиров, {carbs} углеводов"

def format_daily_totals(dishes: list) -> dict:
    """Считает итоговые КБЖУ за день"""
    totals = {
        'calories': 0,
        'protein': 0,
        'fat': 0,
        'carbs': 0,
        'count': len(dishes)
    }
    
    for dish in dishes:
        totals['calories'] += dish['calories']
        totals['protein'] += dish['protein']
        totals['fat'] += dish['fat']
        totals['carbs'] += dish['carbs']
    
    return totals

def format_totals_text(totals: dict) -> str:
    """Форматирует итоги для вывода"""
    return f"{totals['calories']} ккал, {totals['protein']} белков, {totals['fat']} жиров, {totals['carbs']} углеводов"