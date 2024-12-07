import streamlit as st
import base64
from services.performance_attribution.main import PerformanceAttribution
import plotly.graph_objects as go


def get_image_as_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def setup_page():
    """Configure page settings and header"""
    st.set_page_config(
        layout="wide",
        page_title="Risky Hayek 🌶️",
        initial_sidebar_state="collapsed",
    )

    # Set Poppins font for titles with less weight
    st.markdown(
        """
        <style>
        .title {
            font-family: 'Poppins', sans-serif;
            font-weight: 500; /* Adjusted font weight for less boldness */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    header_container = st.container()
    with header_container:
        # Use three columns: left logo, space, right logo
        col1, col2, col3 = st.columns([1, 2, 1])

        # Left logo (Fintual)
        with col1:
            try:
                fintual_logo = get_image_as_base64("fintual-logo.png")
                st.markdown(
                    f'<img src="data:image/png;base64,{fintual_logo}" width="150" style="display: block;" />',
                    unsafe_allow_html=True,
                )
            except FileNotFoundError:
                st.error(
                    "Logo file not found. Please make sure 'fintual-logo.png' is in the same directory."
                )

        # Right logo (Hayek)
        with col3:
            try:
                hayek_logo = get_image_as_base64("hayek-logo.png")
                st.markdown(
                    f'<img src="data:image/png;base64,{hayek_logo}" width="150" style="display: block; margin-left: auto;" />',
                    unsafe_allow_html=True,
                )
            except FileNotFoundError:
                st.error(
                    "Logo file not found. Please make sure 'hayek-logo.png' is in the same directory."
                )

    # Separate container for centered titles
    title_container = st.container()
    with title_container:
        st.markdown(
            '<div style="text-align: center; width: 100%; margin-top: 50px;">'  # Centered content
            '<h1 class="title">Cómo va Risky Hayek 🌶️</h1>'
            "</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="text-align: center; width: 100%;">'  # Centered content
            '<p style="margin-top: 20px; font-size: 20px; color: #545e6d; font-family: Poppins, sans-serif; font-weight: 350;">'
            "Rendimientos intradía no oficiales del Fondo de Inversión más cabrón de Fintual."
            "</p></div>",
            unsafe_allow_html=True,
        )


def display_total_return(perf_attr):
    """Display the performance metrics with appropriate styling"""
    total_return_mxn = perf_attr.total_return_mxn
    font_color = "#77d5ad" if total_return_mxn >= 0 else "#ee6c61"
    st.markdown(
        f'<p style="text-align: left; font-size: 28px; margin-top: 50px;">Hasta ahora el rendimiento de Hayek es <span style="color: {font_color};">{(total_return_mxn*100):.2f}%</span></p>',
        unsafe_allow_html=True,
    )


def display_attribution_table(perf_attr):
    """Display the attribution dataframe as a styled table"""
    # Create a copy of the dataframe to avoid modifying the original
    columns_to_display = [
        "name",
        "weight",
        "start_price",
        "end_price",
        "return_usd",
        "return_mxn",
    ]
    df_styled = perf_attr.attribution_df[columns_to_display].copy()
    df_styled = df_styled.sort_values(by="weight", ascending=False)

    # Convert percentages
    df_styled.loc[:, ["weight", "return_usd", "return_mxn"]] = (
        df_styled.loc[:, ["weight", "return_usd", "return_mxn"]] * 100
    )

    # Function to apply color based on value
    def color_value(val):
        try:
            color = "#77d5ad" if float(val) >= 0 else "#ee6c61"
            return f"color: {color}"
        except (ValueError, TypeError):
            return ""

    # Rename columns before styling
    df_styled.columns = [
        "Instrumento",
        "Peso (%)",
        "Precio Inicial",
        "Precio Actual",
        "Rendimiento USD",
        "Rendimiento MXN",
    ]

    # Create the style
    styled_df = df_styled.style.map(  # Changed from applymap to map
        color_value,
        subset=["Rendimiento USD", "Rendimiento MXN"],
    )

    # Apply formatting
    styled_df.set_properties(**{"text-align": "left"})
    styled_df.set_table_styles(
        [{"selector": "th", "props": [("text-align", "left")]}]
    )
    styled_df.format(
        {
            "Peso (%)": "{:.2f}%",
            "Rendimiento USD": "{:.2f}%",
            "Rendimiento MXN": "{:.2f}%",
            "Precio Inicial": "{:.2f}",
            "Precio Actual": "{:.2f}",
        }
    )

    # Display the styled table with dynamic height
    st.markdown("### Desglose por instrumento")
    # Calculate height: ~35px per row + 35px for header
    row_height = 35
    header_height = 35
    dynamic_height = (len(df_styled) * row_height) + header_height
    st.dataframe(styled_df, use_container_width=True, height=dynamic_height)


def display_contribution_chart():
    """Display horizontal bar charts showing contributions"""
    st.markdown("### Contribución por tipo")

    # Create two columns for the charts
    col1, col2 = st.columns(2)

    # Calculate dynamic height based on number of instruments
    # Allow ~30px per instrument with a minimum of 200px
    num_instruments = len(performance_attribution.attribution_df)
    chart_height = max(200, num_instruments * 30)

    with col1:
        # First chart (original FX and Equity effects)
        labels = ["Acciones", "Tipo de Cambio"]
        values = [
            performance_attribution.total_equity_effect * 100,
            performance_attribution.total_fx_effect * 100,
        ]

        colors = ["#77d5ad" if val >= 0 else "#ee6c61" for val in values]

        fig1 = go.Figure(
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color=colors,
                text=[f"{val:+.2f}%" for val in values],
                textposition="auto",
            )
        )

        fig1.update_layout(
            height=chart_height,
            margin=dict(l=0, r=0, t=20, b=20),
            xaxis_title="Contribución (%)",
            showlegend=False,
            plot_bgcolor="white",
        )

        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        # Second chart (instrument contributions)
        df_contributions = performance_attribution.attribution_df.sort_values(
            "ctr_mxn", ascending=True
        )
        labels = df_contributions["name"]
        values = df_contributions["ctr_mxn"] * 100  # Convert to percentage

        colors = ["#77d5ad" if val >= 0 else "#ee6c61" for val in values]

        fig2 = go.Figure(
            go.Bar(
                x=values,
                y=labels,
                orientation="h",
                marker_color=colors,
                text=[f"{val:+.2f}%" for val in values],
                textposition="auto",
            )
        )

        fig2.update_layout(
            height=chart_height,
            margin=dict(l=0, r=0, t=20, b=20),
            xaxis_title="Contribución (%)",
            showlegend=False,
            plot_bgcolor="white",
            yaxis=dict(
                tickmode="linear",  # Show all ticks
                dtick=1,  # Space between ticks
            ),
        )

        st.plotly_chart(fig2, use_container_width=True)


def display_intraday_returns_chart(perf_attr):
    """Display a timeseries chart of intraday portfolio returns"""
    st.markdown("### Rendimiento en vivo 🔥")

    # Get the timeseries data
    returns = perf_attr.intraday_portfolio_returns

    # Create the line chart
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=returns.index,
            y=returns,
            mode="lines",
            line=dict(
                color="#77d5ad" if returns.iloc[-1] >= 0 else "#ee6c61", width=2
            ),
            hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>",
        )
    )

    # Update layout
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=20, b=20),
        yaxis_title="Rendimiento (%)",
        showlegend=False,
        plot_bgcolor="white",
        yaxis=dict(
            gridcolor="rgba(0,0,0,0.1)",
            zerolinecolor="rgba(0,0,0,0.2)",
        ),
        xaxis=dict(
            gridcolor="rgba(0,0,0,0.1)",
        ),
    )

    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":

    setup_page()

    with st.spinner(
        "Cargando datos..."
    ):  # Add loading spinner with Spanish text
        performance_attribution = PerformanceAttribution()

    display_total_return(performance_attribution)
    display_intraday_returns_chart(performance_attribution)
    display_contribution_chart()
    display_attribution_table(performance_attribution)

    # Add lorem ipsum paragraph
    st.markdown(
        '<div style="text-align: center; width: 100%; margin-top: 50px; margin-bottom: 50px;">'
        '<p style="font-size: 14px; color: #888888; font-family: Poppins, sans-serif;">'
        "¿Quién es Risky Hayek? Risky Hayek es un fondo de inversión que invierte en acciones de todo el mundo. "
        "No sabemos su origen, la teoría más antigua dice que proviene de Salma Hayek, "
        "otros proponen que es el alma de Friedrich Hayek encarnada en un robot androide "
        "pero no hay pruebas de ello. Algunos dicen que es un señor de los desiertos, "
        "otros que es una señorita de la selva, pero lo que sí sabemos es que es muy rico y le encanta el chile."
        "</p></div>",
        unsafe_allow_html=True,
    )
