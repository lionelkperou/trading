import base64
import io
from flask import render_template, request, flash, redirect, url_for, session
from app import app
from app.strategies import get_stock_data, bollinger_bands, moving_average_crossover, calculate_returns
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
# Liste des symboles d'actions (vous pouvez l'étendre ou la charger depuis une source externe)
STOCK_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'FB', 'TSLA', 'NVDA', 'JPM', 'JNJ', 'V']

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def determine_best_strategy(bb_return, ma_return, bb_sharpe, ma_sharpe, bb_drawdown, ma_drawdown):
    score_bb = 0
    score_ma = 0
    
    # Comparaison des rendements
    if bb_return != "N/A" and ma_return != "N/A":
        if float(bb_return) > float(ma_return):
            score_bb += 1
        elif float(ma_return) > float(bb_return):
            score_ma += 1
    
    # Comparaison des ratios de Sharpe
    if bb_sharpe != "N/A" and ma_sharpe != "N/A":
        if float(bb_sharpe) > float(ma_sharpe):
            score_bb += 1
        elif float(ma_sharpe) > float(bb_sharpe):
            score_ma += 1
    
    # Comparaison des drawdowns maximaux
    if bb_drawdown != "N/A" and ma_drawdown != "N/A":
        if float(bb_drawdown) < float(ma_drawdown):
            score_bb += 1
        elif float(ma_drawdown) < float(bb_drawdown):
            score_ma += 1
    
    if score_bb > score_ma:
        return "Bandes de Bollinger"
    elif score_ma > score_bb:
        return "Croisement des moyennes mobiles"
    else:
        return "Les deux stratégies sont équivalentes"

def generate_justification(best_strategy, bb_return, ma_return, bb_sharpe, ma_sharpe, bb_drawdown, ma_drawdown):
    justification = f"La stratégie {best_strategy} a été choisie car elle offre "
    
    if best_strategy == "Bandes de Bollinger":
        if bb_return != "N/A" and ma_return != "N/A" and float(bb_return) > float(ma_return):
            justification += f"un meilleur rendement ({bb_return}% contre {ma_return}%), "
        if bb_sharpe != "N/A" and ma_sharpe != "N/A" and float(bb_sharpe) > float(ma_sharpe):
            justification += f"un meilleur ratio de Sharpe ({bb_sharpe} contre {ma_sharpe}), "
        if bb_drawdown != "N/A" and ma_drawdown != "N/A" and float(bb_drawdown) < float(ma_drawdown):
            justification += f"un drawdown maximal plus faible ({bb_drawdown}% contre {ma_drawdown}%), "
    elif best_strategy == "Croisement des moyennes mobiles":
        if ma_return != "N/A" and bb_return != "N/A" and float(ma_return) > float(bb_return):
            justification += f"un meilleur rendement ({ma_return}% contre {bb_return}%), "
        if ma_sharpe != "N/A" and bb_sharpe != "N/A" and float(ma_sharpe) > float(bb_sharpe):
            justification += f"un meilleur ratio de Sharpe ({ma_sharpe} contre {bb_sharpe}), "
        if ma_drawdown != "N/A" and bb_drawdown != "N/A" and float(ma_drawdown) < float(bb_drawdown):
            justification += f"un drawdown maximal plus faible ({ma_drawdown}% contre {bb_drawdown}%), "
    else:
        justification = "Les deux stratégies présentent des performances similaires. "
    
    justification = justification.rstrip(", ") + "."
    return justification

def generate_risk_considerations(best_strategy, bb_drawdown, ma_drawdown):
    considerations = "Tenez compte des éléments suivants lors de l'utilisation de cette stratégie : "
    
    if best_strategy == "Bandes de Bollinger":
        considerations += f"Le drawdown maximal pour cette stratégie est de {bb_drawdown}%. "
        considerations += "Les Bandes de Bollinger peuvent être moins efficaces dans des marchés très tendanciels. "
    elif best_strategy == "Croisement des moyennes mobiles":
        considerations += f"Le drawdown maximal pour cette stratégie est de {ma_drawdown}%. "
        considerations += "La stratégie de croisement des moyennes mobiles peut générer de faux signaux dans des marchés sans tendance claire. "
    else:
        considerations += f"Les drawdowns maximaux sont de {bb_drawdown}% pour les Bandes de Bollinger et de {ma_drawdown}% pour le Croisement des moyennes mobiles. "
        considerations += "Chaque stratégie a ses propres forces et faiblesses selon les conditions du marché. "
    
    considerations += "Assurez-vous de diversifier vos investissements et d'utiliser une gestion de risque appropriée."
    return considerations

@app.route('/')
def accueil():
    return render_template('accueil.html')

@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        df = None
        symbol = None

        if 'file' in request.files:
            # Traitement du formulaire de fichier
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filename)
                df = pd.read_csv(filename) if filename.endswith('.csv') else pd.read_excel(filename)
                os.remove(filename)  # Supprime le fichier après l'avoir lu
                
                # Assurez-vous que la colonne de date est l'index et au bon format
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                elif not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                
                symbol = 'Fichier uploadé'
                
            else:
                flash('Format de fichier non autorisé. Utilisez .csv ou .xlsx')
                return redirect(url_for('index'))
        elif 'symbol' in request.form:
            # Traitement du formulaire de symbole
            symbol = request.form['symbol']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            df = get_stock_data(symbol, start_date, end_date)
            
        else:
            flash('Veuillez soit choisir un symbole, soit uploader un fichier.')
            return redirect(url_for('index'))
        
        if df is not None and not df.empty:
           
            # Appliquer les stratégies
            df = bollinger_bands(df)
            df = moving_average_crossover(df)
            df, performance_metrics = calculate_returns(df)
            
    
            # Générer les signaux d'achat et de vente
            df['BB_Buy_Signal'] = np.where((df['BB_Signal'] == 1) & (df['BB_Signal'].shift(1) != 1), df['Close'], np.nan)
            df['BB_Sell_Signal'] = np.where((df['BB_Signal'] == -1) & (df['BB_Signal'].shift(1) != -1), df['Close'], np.nan)
            df['MA_Buy_Signal'] = np.where((df['MA_Signal'] == 1) & (df['MA_Signal'].shift(1) != 1), df['Close'], np.nan)
            df['MA_Sell_Signal'] = np.where((df['MA_Signal'] == -1) & (df['MA_Signal'].shift(1) != -1), df['Close'], np.nan)

            # Formater les données pour le graphique
            dates = df.index.strftime('%Y-%m-%d').tolist()
            chart_data = {
                'dates': dates,
                'close': df['Close'].tolist(),
                'upper_bb': df['Upper_BB'].tolist(),
                'lower_bb': df['Lower_BB'].tolist(),
                'sma_short': df['SMA_Short'].tolist(),
                'sma_long': df['SMA_Long'].tolist(),
                'bb_returns': df['bb_cumulative_return'].tolist(),
                'ma_returns': df['ma_cumulative_return'].tolist(),
                'bb_buy_signals': [{'x': date, 'y': price} for date, price in zip(dates, df['BB_Buy_Signal']) if not pd.isna(price)],
                'bb_sell_signals': [{'x': date, 'y': price} for date, price in zip(dates, df['BB_Sell_Signal']) if not pd.isna(price)],
                'ma_buy_signals': [{'x': date, 'y': price} for date, price in zip(dates, df['MA_Buy_Signal']) if not pd.isna(price)],
                'ma_sell_signals': [{'x': date, 'y': price} for date, price in zip(dates, df['MA_Sell_Signal']) if not pd.isna(price)],
            }

              # Calculer les rendements cumulatifs finaux
            bb_return = df['bb_cumulative_return'].iloc[-1] * 100 if not df['bb_cumulative_return'].empty else np.nan
            ma_return = df['ma_cumulative_return'].iloc[-1] * 100 if not df['ma_cumulative_return'].empty else np.nan
            
             
            # Formater les rendements
            bb_return = "N/A" if np.isnan(bb_return) else f"{bb_return:.2f}"
            ma_return = "N/A" if np.isnan(ma_return) else f"{ma_return:.2f}"
            
            # Formater les métriques de performance
            for key in performance_metrics:
                if np.isnan(performance_metrics[key]):
                    performance_metrics[key] = "N/A"
                elif key.endswith('_drawdown'):
                    performance_metrics[key] = f"{performance_metrics[key] * 100:.2f}"
                else:
                    performance_metrics[key] = f"{performance_metrics[key]:.2f}"
          
           # Déterminer la meilleure stratégie et générer les recommandations
            overall_best_strategy = determine_best_strategy(
                bb_return, ma_return,
                performance_metrics['bb_sharpe'], performance_metrics['ma_sharpe'],
                performance_metrics['bb_max_drawdown'], performance_metrics['ma_max_drawdown']
            )
            
            strategy_justification = generate_justification(
                overall_best_strategy,
                bb_return, ma_return,
                performance_metrics['bb_sharpe'], performance_metrics['ma_sharpe'],
                performance_metrics['bb_max_drawdown'], performance_metrics['ma_max_drawdown']
            )
            
            risk_considerations = generate_risk_considerations(
                overall_best_strategy,
                performance_metrics['bb_max_drawdown'], performance_metrics['ma_max_drawdown']
            )
         
            return render_template('result.html', 
                                   chart_data=json.dumps(chart_data), 
                                   symbol=symbol,
                                   bb_return=bb_return,
                                   ma_return=ma_return,
                                   performance_metrics=performance_metrics,
                                   overall_best_strategy=overall_best_strategy,
                                   strategy_justification=strategy_justification,
                                   risk_considerations=risk_considerations)
        else:
            flash('Aucune donnée valide n\'a été trouvée. Veuillez vérifier votre fichier ou le symbole saisi.')
            return redirect(url_for('index'))
    
    return render_template('index.html', symbols=STOCK_SYMBOLS)


# Page des recommandations
@app.route("/recommandations", methods=["GET", "POST"])
def recommandations():
    if request.method == "POST":
        # Récupération des données du formulaire
        risk_tolerance = request.form.get("riskTolerance")
        investment_preference = request.form.get("investmentPreference")
        capital = request.form.get("capital")

        # Génération des recommandations (simple logique)
        if risk_tolerance == "low":
            strategy = "Investissez dans des obligations ou ETF à faible risque."
        elif risk_tolerance == "medium":
            strategy = "Considérez un portefeuille équilibré avec des actions et obligations."
        else:
            strategy = "Explorez des actions de croissance et des investissements à haut risque."

        if investment_preference == "shortTerm":
            strategy += " Adoptez une stratégie à court terme (ex. : swing trading)."
        else:
            strategy += " Pensez à des placements à long terme (ex. : buy and hold)."

        # Retour des recommandations
        return render_template("recommandations_result.html", strategy=strategy, capital=capital)

    return render_template("recommandations.html")



@app.route("/apropos")
def apropos():
    return render_template("apropos.html")
    
@app.route("/avertissement")
def avertissement():
    return render_template("avertissement.html")


        
