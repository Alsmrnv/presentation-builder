"""
Pydantic схемы для валидации JSON от LLM

ИСПОЛЬЗОВАНИЕ:
1. Основная LLM определяет тип нужной визуализации
2. Вызываем validate_llm_response(vis_type, json_data)
3. Функция использует соответствующую схему для валидации
4. Получаем валидированные данные или понятную ошибку

Пример:
    from visgen.schemas import validate_llm_response

    # LLM решила что нужен bar chart
    vis_type = "bar"
    llm_json = {...}  # JSON от LLM

    try:
        validated_data = validate_llm_response(vis_type, llm_json)
        # Передаем в рендер...
    except ValueError as e:
        # Отправляем ошибку обратно LLM
        error_message = f"Please fix JSON: {e}"

    # LLM решила что нужен scatter chart
    vis_type = "scatter"

    # LLM решила что нужен histogram
    vis_type = "histogram"

    # LLM решила что нужен table
    vis_type = "table"
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Any, Optional


class BaseVisualizationSchema(BaseModel):
    """Базовая схема всех визуализаций"""
    model_config = ConfigDict(extra='forbid')

    type: str = Field("plotly", pattern="^plotly$")
    chart_type: str
    data: dict[str, Any]
    layout: Optional[dict[str, Any]] = Field(default_factory=dict)


class LineChartSchema(BaseVisualizationSchema):
    """Схема для линейного графика"""
    chart_type: str = Field("line", pattern="^line$")

    @field_validator('data')
    @classmethod
    def validate_line_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        if 'x' not in v or 'y' not in v:
            raise ValueError('Line chart must have x and y arrays')

        x, y = v['x'], v['y']

        if len(x) != len(y):
            raise ValueError('X and Y arrays must have same length')
        if len(x) > 20:
            raise ValueError('Maximum 20 data points allowed')
        if not all(isinstance(item, (int, float)) for item in y):
            raise ValueError('Y array must contain only numbers')

        return v


class BarChartSchema(BaseVisualizationSchema):
    """Схема для столбчатой диаграммы"""
    chart_type: str = Field("bar", pattern="^bar$")

    @field_validator('data')
    @classmethod
    def validate_bar_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        if 'x' not in v or 'y' not in v:
            raise ValueError('Bar chart must have x and y arrays')

        x, y = v['x'], v['y']

        if len(x) != len(y):
            raise ValueError('X and Y arrays must have same length')
        if len(x) > 20:
            raise ValueError('Maximum 20 bars allowed')
        if not all(isinstance(item, (int, float)) for item in y):
            raise ValueError('Y array must contain only numbers')
        if not all(isinstance(item, str) for item in x):
            raise ValueError('X array must contain only strings')

        return v

class PieChartSchema(BaseVisualizationSchema):
    """Схема для круговой диаграммы"""
    chart_type: str = Field("pie", pattern="^pie$")

    @field_validator('data')
    @classmethod
    def validate_pie_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        if 'labels' not in v or 'values' not in v:
            raise ValueError('Pie chart must have labels and values arrays')

        labels, values = v['labels'], v['values']

        if len(labels) != len(values):
            raise ValueError('Labels and values arrays must have same length')
        if len(labels) > 10:
            raise ValueError('Maximum 10 segments allowed')
        if not all(isinstance(item, (int, float)) and item >= 0 for item in values):
            raise ValueError('Values array must contain only non-negative numbers')
        if not all(isinstance(item, str) for item in labels):
            raise ValueError('Labels array must contain only strings')

        return v

class ScatterChartSchema(BaseVisualizationSchema):
    """Схема для точечной диаграммы"""
    chart_type: str = Field("scatter", pattern="^scatter$")

    @field_validator('data')
    @classmethod
    def validate_scatter_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        if 'x' not in v or 'y' not in v:
            raise ValueError('Scatter chart must have x and y arrays')

        x, y = v['x'], v['y']

        if len(x) != len(y):
            raise ValueError('X and Y arrays must have same length')
        if len(x) > 100:
            raise ValueError('Maximum 100 data points allowed')
        if not all(isinstance(item, (int, float)) for item in x):
            raise ValueError('X array must contain only numbers')
        if not all(isinstance(item, (int, float)) for item in y):
            raise ValueError('Y array must contain only numbers')

        return v

class HistogramSchema(BaseVisualizationSchema):
    """Схема для гистограммы"""
    chart_type: str = Field("histogram", pattern="^histogram$")

    @field_validator('data')
    @classmethod
    def validate_histogram_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        if 'x' not in v:
            raise ValueError('Histogram must have x array')

        x = v['x']

        if len(x) > 1000:
            raise ValueError('Maximum 1000 data points allowed')
        if not all(isinstance(item, (int, float)) for item in x):
            raise ValueError('X array must contain only numbers')

        return v

class TableSchema(BaseVisualizationSchema):
    """Схема для таблицы"""
    chart_type: str = Field("table", pattern="^table$")

    @field_validator('data')
    @classmethod
    def validate_table_data(cls, v: dict[str, Any]) -> dict[str, Any]:
        if 'header' not in v or 'cells' not in v:
            raise ValueError('Table must have header and cells arrays')

        header, cells = v['header'], v['cells']

        if not all(isinstance(item, str) for item in header):
            raise ValueError('Header array must contain only strings')
        if len(header) > 20:
            raise ValueError('Maximum 20 columns allowed')
        if len(cells) > 100:
            raise ValueError('Maximum 100 rows allowed')
        if not all(isinstance(row, list) for row in cells):
            raise ValueError('Cells must be array of arrays')

        for row in cells:
            if len(row) != len(header):
                raise ValueError(f'Row has {len(row)} cells, but header has {len(header)} columns')
            if not all(isinstance(item, str) for item in row):
                raise ValueError('All cells must contain only strings')

        return v


def validate_llm_response(vis_type: str, json_data: dict[str, Any]) -> BaseVisualizationSchema:
    """
    Универсальная функция валидации JSON от LLM
    """
    visualization_schemas: dict[str, type[BaseVisualizationSchema]] = {
        "line": LineChartSchema,
        "bar": BarChartSchema,
        "pie": PieChartSchema,
        "scatter": ScatterChartSchema,
        "histogram": HistogramSchema,
        "table": TableSchema,
    }

    if vis_type not in visualization_schemas:
        available_types = list(visualization_schemas.keys())
        raise ValueError(f"Unsupported visualization type: {vis_type}. Available: {available_types}")

    schema_class = visualization_schemas[vis_type]
    try:
        return schema_class(**json_data)
    except Exception as e:
        raise ValueError(str(e))