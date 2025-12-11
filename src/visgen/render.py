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
        """Создает КОМПАКТНЫЙ линейный график"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            mode='lines+markers',
            name=chart_data.data.get('series_name', 'Data'),
            line=dict(width=2.5, color='#1f77b4'),
            marker=dict(size=6, color='#d62728', line=dict(width=1, color='black'))
        ))

        layout_without_title = chart_data.layout.copy() if chart_data.layout else {}
        if 'title' in layout_without_title:
            del layout_without_title['title']

        return self._apply_compact_layout(fig, chart_data.layout, 'line')

    def _create_bar_chart(self, chart_data: BarChartSchema) -> go.Figure:
        """Создает КОМПАКТНУЮ столбчатую диаграмму"""
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        fig.add_trace(go.Bar(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            name=chart_data.data.get('series_name', 'Values'),
            marker_color=colors[:len(chart_data.data['x'])],
            marker_line_color='black',
            marker_line_width=1,
            opacity=0.8,
            text=chart_data.data['y'], 
            textposition='auto',
        ))

        layout_without_title = chart_data.layout.copy() if chart_data.layout else {}
        if 'title' in layout_without_title:
            del layout_without_title['title']

        return self._apply_compact_layout(fig, chart_data.layout, 'bar')

    def _create_pie_chart(self, chart_data: PieChartSchema) -> go.Figure:
        """Создает КОМПАКТНУЮ круговую диаграмму"""
        fig = go.Figure()
        
        fig.add_trace(go.Pie(
            labels=chart_data.data['labels'],
            values=chart_data.data['values'],
            name=chart_data.data.get('series_name', 'Values'),
            hole=0.4 if len(chart_data.data['labels']) > 3 else 0.3,
            marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
                               '#9467bd', '#8c564b', '#e377c2']),
            textinfo='percent+label',
            textposition='auto',
        ))
        
        layout_without_title = chart_data.layout.copy() if chart_data.layout else {}
        if 'title' in layout_without_title:
            del layout_without_title['title']

        return self._apply_compact_layout(fig, chart_data.layout, 'pie')

    def _create_scatter_chart(self, chart_data: ScatterChartSchema) -> go.Figure:
        """Создает КОМПАКТНУЮ точечную диаграмму"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=chart_data.data['x'],
            y=chart_data.data['y'],
            mode='markers',
            name=chart_data.data.get('series_name', 'Data'),
            marker=dict(size=10, opacity=0.7, color='#1f77b4')
        ))

        layout_without_title = chart_data.layout.copy() if chart_data.layout else {}
        if 'title' in layout_without_title:
            del layout_without_title['title']

        return self._apply_compact_layout(fig, chart_data.layout, 'scatter')

    def _create_histogram(self, chart_data: HistogramSchema) -> go.Figure:
        """Создает КОМПАКТНУЮ гистограмму"""
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=chart_data.data['x'],
            name=chart_data.data.get('series_name', 'Values'),
            nbinsx=20,
            marker_color='lightseagreen',
            opacity=0.7
        ))

        layout_without_title = chart_data.layout.copy() if chart_data.layout else {}
        if 'title' in layout_without_title:
            del layout_without_title['title']

        return self._apply_compact_layout(fig, chart_data.layout, 'histogram')

    def _create_table(self, chart_data: TableSchema) -> go.Figure:
        """Создает таблицу с оптимальным размером для слайда"""
        fig = go.Figure()
        
        num_cols = len(chart_data.data['header'])
        num_rows = len(chart_data.data['cells'])
        
        if num_cols > 5 or num_rows > 10:
            header_font_size = 7
            cell_font_size = 6
            header_height = 25
            cell_height = 20
            line_width = 60 
        elif num_cols > 3 or num_rows > 5:
            header_font_size = 9
            cell_font_size = 8
            header_height = 30
            cell_height = 25
            line_width = 50
        else:
            header_font_size = 14
            cell_font_size = 12
            header_height = 35
            cell_height = 30
            line_width = 40
        
        def add_word_wrap(text, max_line_length):
            if not isinstance(text, str):
                return str(text)
            if len(text) <= max_line_length:
                return text
            
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= max_line_length:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return '<br>'.join(lines)
        
        wrapped_headers = [add_word_wrap(h, line_width // 2) for h in chart_data.data['header']]
        
        wrapped_cells = []
        for col_idx in range(num_cols):
            column_data = []
            for row_idx in range(num_rows):
                if row_idx < len(chart_data.data['cells']):
                    cell_value = chart_data.data['cells'][row_idx][col_idx]
                    wrapped = add_word_wrap(cell_value, line_width)
                    column_data.append(wrapped)
            wrapped_cells.append(column_data)
        
        fig.add_trace(go.Table(
            header=dict(
                values=wrapped_headers,
                align='center',
                fill_color='lightgrey',
                font=dict(
                    size=header_font_size, 
                    color='black', 
                    family="Arial",
                ),
                height=header_height,
                line=dict(width=1, color='black'),
            ),
            cells=dict(
                values=wrapped_cells if chart_data.data['cells'] else [],
                align='center',
                fill_color='white',
                font=dict(
                    size=cell_font_size, 
                    color='black', 
                    family="Arial",
                ),
                height=cell_height,
                line=dict(width=1, color='black'),
                format=None,
            )
        ))
        
        layout_without_title = chart_data.layout.copy() if chart_data.layout else {}
        if 'title' in layout_without_title:
            del layout_without_title['title']
        
        return self._apply_compact_layout(fig, layout_without_title, 'table')

    def _apply_compact_layout(self, fig: go.Figure, layout: Optional[dict], chart_type: str) -> go.Figure:
        """Применяет КОМПАКТНЫЙ layout для графиков"""
        
        layout_config = {
            'paper_bgcolor': 'white',
            'plot_bgcolor': 'white',
            'font': dict(family="Arial", size=11, color='black'),
            'showlegend': False, 
        }
        
        if chart_type == 'bar':
            layout_config.update({
                'width': 500, 
                'height': 350,
                'margin': dict(l=50, r=30, t=40, b=60), 
                'xaxis': dict(
                    title_font=dict(size=11),
                    tickfont=dict(size=10),
                    tickangle=-45 if len(fig.data[0].x) > 5 else 0
                ),
                'yaxis': dict(
                    title_font=dict(size=11),
                    tickfont=dict(size=10),
                    gridcolor='lightgrey',
                    gridwidth=0.5
                )
            })
        elif chart_type == 'line':
            layout_config.update({
                'width': 550,
                'height': 350,
                'margin': dict(l=50, r=30, t=40, b=60),
                'xaxis': dict(
                    title_font=dict(size=11),
                    tickfont=dict(size=10),
                    gridcolor='lightgrey',
                    gridwidth=0.5
                ),
                'yaxis': dict(
                    title_font=dict(size=11),
                    tickfont=dict(size=10),
                    gridcolor='lightgrey',
                    gridwidth=0.5
                )
            })
        elif chart_type == 'pie':
            layout_config.update({
                'width': 450,  
                'height': 350,
                'margin': dict(l=20, r=20, t=40, b=20),
            })
        elif chart_type == 'scatter':
            layout_config.update({
                'width': 550,
                'height': 350,
                'margin': dict(l=50, r=30, t=40, b=60),
                'xaxis': dict(
                    title_font=dict(size=11),
                    tickfont=dict(size=10),
                    gridcolor='lightgrey',
                    gridwidth=0.5
                ),
                'yaxis': dict(
                    title_font=dict(size=11),
                    tickfont=dict(size=10),
                    gridcolor='lightgrey',
                    gridwidth=0.5
                )
            })
        elif chart_type == 'histogram':
            layout_config.update({
                'width': 550,
                'height': 350,
                'margin': dict(l=50, r=30, t=40, b=60),
                'xaxis': dict(
                    title_font=dict(size=11),
                    tickfont=dict(size=10)
                ),
                'yaxis': dict(
                    title_font=dict(size=11),
                    tickfont=dict(size=10),
                    gridcolor='lightgrey',
                    gridwidth=0.5
                )
            })
        elif chart_type == 'table':
            layout_config.update({
                'width': 700, 
                'height': 400,
                'margin': dict(l=5, r=5, t=5, b=5),  
            })
        
        if layout:
            if 'title' in layout and chart_type != 'table':
                layout_config['title'] = {
                    'text': layout['title'],
                    'font': dict(size=13, family="Arial", color='black'),
                    'x': 0.5,
                    'xanchor': 'center',
                    'y': 0.95
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
        
        Raises:
            ValueError: если не удалось создать PNG
        """
        try:
            width = fig.layout.width or 800
            height = fig.layout.height or 500
            
            img_bytes = to_image(
                fig, 
                format='png', 
                width=width, 
                height=height, 
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