// static/js/charts.js
document.addEventListener('DOMContentLoaded', function() {
    const trace1 = {
        x: chartData.dates,
        y: chartData.close,
        type: 'scatter',
        mode: 'lines',
        name: 'Prix de clôture'
    };

    const trace2 = {
        x: chartData.dates,
        y: chartData.upper_bb,
        type: 'scatter',
        mode: 'lines',
        name: 'Bande supérieure de Bollinger',
        line: {color: 'rgba(200, 0, 0, 0.5)'}
    };

    const trace3 = {
        x: chartData.dates,
        y: chartData.lower_bb,
        type: 'scatter',
        mode: 'lines',
        name: 'Bande inférieure de Bollinger',
        line: {color: 'rgba(200, 0, 0, 0.5)'}
    };

    const trace4 = {
        x: chartData.dates,
        y: chartData.sma_short,
        type: 'scatter',
        mode: 'lines',
        name: 'MM courte',
        line: {color: 'rgba(0, 200, 0, 0.5)'}
    };

    const trace5 = {
        x: chartData.dates,
        y: chartData.sma_long,
        type: 'scatter',
        mode: 'lines',
        name: 'MM longue',
        line: {color: 'rgba(0, 0, 200, 0.5)'}
    };

    const trace6 = {
        x: chartData.dates,
        y: chartData.bb_returns,
        type: 'scatter',
        mode: 'lines',
        name: 'Rendements Bollinger',
        yaxis: 'y2'
    };

    const trace7 = {
        x: chartData.dates,
        y: chartData.ma_returns,
        type: 'scatter',
        mode: 'lines',
        name: 'Rendements MM',
        yaxis: 'y2'
    };

    // Nouveaux traces pour les signaux
    const traceBBBuy = {
        x: chartData.bb_buy_signals.map(point => point.x),
        y: chartData.bb_buy_signals.map(point => point.y),
        type: 'scatter',
        mode: 'markers',
        name: 'Signaux d\'achat Bollinger',
        marker: {
            color: 'green',
            size: 10,
            symbol: 'triangle-up'
        }
    };

    const traceBBSell = {
        x: chartData.bb_sell_signals.map(point => point.x),
        y: chartData.bb_sell_signals.map(point => point.y),
        type: 'scatter',
        mode: 'markers',
        name: 'Signaux de vente Bollinger',
        marker: {
            color: 'red',
            size: 10,
            symbol: 'triangle-down'
        }
    };

    const traceMABuy = {
        x: chartData.ma_buy_signals.map(point => point.x),
        y: chartData.ma_buy_signals.map(point => point.y),
        type: 'scatter',
        mode: 'markers',
        name: 'Signaux d\'achat MM',
        marker: {
            color: 'blue',
            size: 10,
            symbol: 'triangle-up'
        }
    };

    const traceMASell = {
        x: chartData.ma_sell_signals.map(point => point.x),
        y: chartData.ma_sell_signals.map(point => point.y),
        type: 'scatter',
        mode: 'markers',
        name: 'Signaux de vente MM',
        marker: {
            color: 'orange',
            size: 10,
            symbol: 'triangle-down'
        }
    };

    const layout = {
        title: 'Comparaison des stratégies',
        yaxis: {title: 'Prix'},
        yaxis2: {
            title: 'Rendements cumulatifs',
            overlaying: 'y',
            side: 'right'
        },
        legend: {orientation: 'h', y: -0.2},
        height: 600  // Augmente la hauteur du graphique
    };

    Plotly.newPlot('chart', [trace1, trace2, trace3, trace4, trace5, trace6, trace7, traceBBBuy, traceBBSell, traceMABuy, traceMASell], layout);
});