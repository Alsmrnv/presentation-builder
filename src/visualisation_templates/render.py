"""
Рендерер для преобразования валидированных данных в HTML графики

ИСПОЛЬЗОВАНИЕ:
    from visgen.renderer import render_visualization
    from visgen.schemas import validate_llm_response

    # Валидируем данные
    validated_data = validate_llm_response("bar", llm_json)

    # Рендерим в HTML
    html_path = render_visualization(validated_data, "output/chart.html")

    # Валидируем данные
    validated_data = validate_llm_response("scatter", llm_json)

    # Валидируем данные
    validated_data = validate_llm_response("histogram", llm_json)

    # Валидируем данные
    validated_data = validate_llm_response("table", llm_json)
"""

import plotly.graph_objects as go
from pathlib import Path
from typing import Union

from .schemas import BaseVisualizationSchema, LineChartSchema, BarChartSchema, PieChartSchema, ScatterChartSchema, HistogramSchema, TableSchema

class Renderer:
    """Базовый класс для рендеринга визуализаций"""

    def __init__(self):
        self.supported_types = {"line", "bar", "pie", "scatter", "histogram", "table"}

    def render(self, validated_data: BaseVisualizationSchema, output_path: Union[str, Path]) -> str:
        """
        Основной метод рендеринга
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if validated_data.chart_type not in self.supported_types:
            raise ValueError(f"Unsupported chart type for rendering: {validated_data.chart_type}")

        if validated_data.chart_type == "line":
            return self._render_line_chart(validated_data, output_path)
        elif validated_data.chart_type == "bar":
            return self._render_bar_chart(validated_data, output_path)
        elif validated_data.chart_type == "pie":
            return self._render_pie_chart(validated_data, output_path)
        elif validated_data.chart_type == "scatter":
            return self._render_scatter_chart(validated_data, output_path)
        elif validated_data.chart_type == "histogram":
            return self._render_histogram(validated_data, output_path)
        elif validated_data.chart_type == "table":
            return self._render_table(validated_data, output_path)

        raise ValueError(f"No renderer for chart type: {validated_data.chart_type}")

    def _render_line_chart(self, chart_data: LineChartSchema, output_path: Path) -> str:
        """Рендерит линейный график в HTML"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            mode='lines+markers',
            name=chart_data.data.get('series_name', 'Data')
        ))

        layout_config = {
            'width': 800,
            'height': 400
        }

        if chart_data.layout:
            if 'title' in chart_data.layout:
                layout_config['title'] = chart_data.layout['title']
            if 'xaxis_title' in chart_data.layout:
                layout_config['xaxis_title'] = chart_data.layout['xaxis_title']
            if 'yaxis_title' in chart_data.layout:
                layout_config['yaxis_title'] = chart_data.layout['yaxis_title']

        fig.update_layout(**layout_config)

        fig.write_html(str(output_path))
        return str(output_path)

    def _render_bar_chart(self, chart_data: BarChartSchema, output_path: Path) -> str:
        """Рендерит столбчатую диаграмму в HTML"""
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            name=chart_data.data.get('series_name', 'Values')
        ))

        layout_config = {
            'width': 800,
            'height': 400
        }

        if chart_data.layout:
            if 'title' in chart_data.layout:
                layout_config['title'] = chart_data.layout['title']
            if 'xaxis_title' in chart_data.layout:
                layout_config['xaxis_title'] = chart_data.layout['xaxis_title']
            if 'yaxis_title' in chart_data.layout:
                layout_config['yaxis_title'] = chart_data.layout['yaxis_title']

        fig.update_layout(**layout_config)

        fig.write_html(str(output_path))
        return str(output_path)

    def _render_pie_chart(self, chart_data: PieChartSchema, output_path: Path) -> str:
        """Рендерит круговую диаграмму в HTML"""
        fig = go.Figure()

        fig.add_trace(go.Pie(
            labels=chart_data.data['labels'],
            values=chart_data.data['values'],
            name=chart_data.data.get('series_name', 'Values')
        ))

        layout_config = {
            'width': 800,
            'height': 400
        }

        if chart_data.layout:
            if 'title' in chart_data.layout:
                layout_config['title'] = chart_data.layout['title']

        fig.update_layout(**layout_config)

        fig.write_html(str(output_path))
        return str(output_path)

    def _render_scatter_chart(self, chart_data: ScatterChartSchema, output_path: Path) -> str:
        """Рендерит точечную диаграмму в HTML"""
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            mode='markers',
            name=chart_data.data.get('series_name', 'Data')
        ))

        layout_config = {
            'width': 800,
            'height': 400
        }

        if chart_data.layout:
            if 'title' in chart_data.layout:
                layout_config['title'] = chart_data.layout['title']
            if 'xaxis_title' in chart_data.layout:
                layout_config['xaxis_title'] = chart_data.layout['xaxis_title']
            if 'yaxis_title' in chart_data.layout:
                layout_config['yaxis_title'] = chart_data.layout['yaxis_title']

        fig.update_layout(**layout_config)

        fig.write_html(str(output_path))
        return str(output_path)

    def _render_histogram(self, chart_data: HistogramSchema, output_path: Path) -> str:
        """Рендерит гистограмму в HTML"""
        fig = go.Figure()

        fig.add_trace(go.Histogram(
            x=chart_data.data['x'],
            name=chart_data.data.get('series_name', 'Values')
        ))

        layout_config = {
            'width': 800,
            'height': 400
        }

        if chart_data.layout:
            if 'title' in chart_data.layout:
                layout_config['title'] = chart_data.layout['title']
            if 'xaxis_title' in chart_data.layout:
                layout_config['xaxis_title'] = chart_data.layout['xaxis_title']
            if 'yaxis_title' in chart_data.layout:
                layout_config['yaxis_title'] = chart_data.layout['yaxis_title']

        fig.update_layout(**layout_config)

        fig.write_html(str(output_path))
        return str(output_path)

    def _render_table(self, chart_data: TableSchema, output_path: Path) -> str:
        """Рендерит таблицу в HTML"""
        fig = go.Figure()

        fig.add_trace(go.Table(
            header=dict(
                values=chart_data.data['header'],
                align='center',
                height=30
            ),
            cells=dict(
                values=list(zip(*chart_data.data['cells'])),
                align='center',
                height=25
            )
        ))

        layout_config = {
            'width': 800,
            'height': 400
        }

        if chart_data.layout:
            if 'title' in chart_data.layout:
                layout_config['title'] = chart_data.layout['title']

        fig.update_layout(**layout_config)

        fig.write_html(str(output_path))
        return str(output_path)


_default_renderer = Renderer()


def render_visualization(validated_data: BaseVisualizationSchema, output_path: Union[str, Path]) -> str:
    """
    Упрощенная функция для рендеринга визуализаций
    """
    return _default_renderer.render(validated_data, output_path)
