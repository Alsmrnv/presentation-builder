"""
Рендерер для преобразования валидированных данных в PNG графики
ТОЛЬКО PNG - для вставки в презентации

ИСПОЛЬЗОВАНИЕ:
    from visgen.renderer import render_visualization
    from visgen.schemas import validate_llm_response

    # Валидируем данные
    validated_data = validate_llm_response("bar", llm_json)

    # Рендерим в PNG
    png_path = render_visualization(validated_data, "output/chart.png")
"""

import plotly.graph_objects as go
from plotly.io import to_image
from pathlib import Path
from typing import Union, Optional

from .schemas import BaseVisualizationSchema, LineChartSchema, BarChartSchema, PieChartSchema, ScatterChartSchema, HistogramSchema, TableSchema

class Renderer:
    """Базовый класс для рендеринга визуализаций в PNG"""

    def __init__(self):
        self.supported_types = {"line", "bar", "pie", "scatter", "histogram", "table"}

    def render(self, validated_data: BaseVisualizationSchema, output_path: Union[str, Path]) -> str:
        """
        Основной метод рендеринга В PNG
        
        Args:
            validated_data: валидированные данные визуализации
            output_path: путь для сохранения PNG
        
        Returns:
            Путь к сохраненному PNG файлу
        
        Raises:
            ValueError: если не удалось создать PNG
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if validated_data.chart_type not in self.supported_types:
            raise ValueError(f"Unsupported chart type for rendering: {validated_data.chart_type}")

        fig = self._create_figure(validated_data)
        
        return self._save_as_png(fig, output_path)

    def _create_figure(self, validated_data: BaseVisualizationSchema) -> go.Figure:
        """Создает Plotly фигуру на основе типа визуализации"""
        chart_type = validated_data.chart_type
        
        if chart_type == "line":
            return self._create_line_chart(validated_data)
        elif chart_type == "bar":
            return self._create_bar_chart(validated_data)
        elif chart_type == "pie":
            return self._create_pie_chart(validated_data)
        elif chart_type == "scatter":
            return self._create_scatter_chart(validated_data)
        elif chart_type == "histogram":
            return self._create_histogram(validated_data)
        elif chart_type == "table":
            return self._create_table(validated_data)
        
        raise ValueError(f"No renderer for chart type: {chart_type}")

    def _create_line_chart(self, chart_data: LineChartSchema) -> go.Figure:
        """Создает линейный график"""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            mode='lines+markers',
            name=chart_data.data.get('series_name', 'Data'),
            line=dict(width=3),
            marker=dict(size=8)
        ))
        return self._apply_layout(fig, chart_data.layout)

    def _create_bar_chart(self, chart_data: BarChartSchema) -> go.Figure:
        """Создает столбчатую диаграмму"""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            name=chart_data.data.get('series_name', 'Values'),
            marker_color='royalblue'
        ))
        return self._apply_layout(fig, chart_data.layout)

    def _create_pie_chart(self, chart_data: PieChartSchema) -> go.Figure:
        """Создает круговую диаграмму"""
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=chart_data.data['labels'],
            values=chart_data.data['values'],
            name=chart_data.data.get('series_name', 'Values'),
            hole=0.3 if len(chart_data.data['labels']) > 3 else 0
        ))
        return self._apply_layout(fig, chart_data.layout)

    def _create_scatter_chart(self, chart_data: ScatterChartSchema) -> go.Figure:
        """Создает точечную диаграмму"""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            mode='markers',
            name=chart_data.data.get('series_name', 'Data'),
            marker=dict(size=10, opacity=0.7)
        ))
        return self._apply_layout(fig, chart_data.layout)

    def _create_histogram(self, chart_data: HistogramSchema) -> go.Figure:
        """Создает гистограмму"""
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=chart_data.data['x'],
            name=chart_data.data.get('series_name', 'Values'),
            nbinsx=20,
            marker_color='lightseagreen'
        ))
        return self._apply_layout(fig, chart_data.layout)

    def _create_table(self, chart_data: TableSchema) -> go.Figure:
        """Создает таблицу"""
        fig = go.Figure()
        fig.add_trace(go.Table(
            header=dict(
                values=chart_data.data['header'],
                align='center',
                fill_color='lightgrey',
                font=dict(size=12, color='black'),
                height=35
            ),
            cells=dict(
                values=list(zip(*chart_data.data['cells'])),
                align='center',
                fill_color='white',
                font=dict(size=11, color='black'),
                height=30
            )
        ))
        return self._apply_layout(fig, chart_data.layout)

    def _apply_layout(self, fig: go.Figure, layout: Optional[dict]) -> go.Figure:
        """Применяет настройки layout к фигуре"""
        layout_config = {
            'width': 800,
            'height': 500,
            'margin': dict(l=50, r=50, t=80, b=50),
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'font': dict(family="Arial", size=12, color='black'),
            'title': dict(
                font=dict(size=16, family="Arial", color='black'),
                x=0.5,
                xanchor='center'
            )
        }
        
        if layout:
            if 'title' in layout:
                layout_config['title'] = {
                    'text': layout['title'],
                    'font': dict(size=16, family="Arial", color='black'),
                    'x': 0.5,
                    'xanchor': 'center'
                }
            if 'xaxis_title' in layout:
                layout_config['xaxis_title'] = layout['xaxis_title']
            if 'yaxis_title' in layout:
                layout_config['yaxis_title'] = layout['yaxis_title']
        
        fig.update_layout(**layout_config)
        return fig

    def _save_as_png(self, fig: go.Figure, output_path: Path) -> str:
        """
        Сохраняет фигуру как PNG используя kaleido
        
        Требует: pip install kaleido
        
        Raises:
            ValueError: если не удалось создать PNG
        """
        try:
            img_bytes = to_image(
                fig, 
                format='png', 
                width=800, 
                height=500, 
                scale=2
            )
            
            if not img_bytes:
                raise ValueError("Kaleido returned empty image bytes")
            
            output_path.write_bytes(img_bytes)
            
            if not output_path.exists():
                raise ValueError(f"PNG file was not created: {output_path}")
            
            if output_path.stat().st_size == 0:
                raise ValueError(f"PNG file is empty: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            raise ValueError(f"Failed to save PNG: {e}. Make sure kaleido is installed and Chrome is available.")


_default_renderer = Renderer()


def render_visualization(validated_data: BaseVisualizationSchema, 
                        output_path: Union[str, Path]) -> str:
    """
    Упрощенная функция для рендеринга визуализаций в PNG
    
    Args:
        validated_data: валидированные данные
        output_path: путь для сохранения PNG
    
    Returns:
        Путь к сохраненному PNG файлу
    
    Raises:
        ValueError: если не удалось создать PNG
    """
    return _default_renderer.render(validated_data, output_path)