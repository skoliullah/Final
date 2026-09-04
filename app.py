import streamlit as st
import pandas as pd
import numpy as np

# Page Configuration
st.set_page_config(page_title="Advanced Mathematical Option Jackpot Scanner", page_icon="🎯", layout="centered")

st.title("🎯 Mathematical Option Chain Jackpot Engine")
st.markdown("Upload your Option Chain CSV file and enter the live spot price to compute the ultimate high-probability jackpot strike using advanced mathematical scoring.")

# Sidebar for Live Inputs
st.sidebar.header("Market Parameters")
spot_price = st.sidebar.number_input("Enter Live Spot Price:", value=48050.0, step=1.0)

# File Uploader
uploaded_file = st.file_uploader("Upload Option Chain CSV File", type=["csv"])

if uploaded_file is not None:
    try:
        # Load CSV data
        df = pd.read_csv(uploaded_file)
        
        # Comprehensive required columns check
        required_columns = [
            'Strike', 'Call_OI', 'Call_Chng_OI', 'Call_Volume', 'Call_LTP', 'Call_IV',
            'Put_OI', 'Put_Chng_OI', 'Put_Volume', 'Put_LTP', 'Put_IV'
        ]
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"Missing columns in CSV: {missing_cols}. Please ensure your CSV headers match the required format.")
        else:
            # Clean data: handle missing values or zeroes to avoid division errors
            df = df.fillna(0)
            
            # 1. Identify At-The-Money (ATM) strike closest to the spot price
            df['Distance_From_Spot'] = abs(df['Strike'] - spot_price)
            atm_idx = df['Distance_From_Spot'].idxmin()
            
            # Focus precisely on ATM and immediate OTM/ITM range (± 4 strikes) where explosive gamma/momentum happens
            analysis_df = df.iloc[max(0, atm_idx-4): min(len(df), atm_idx+5)].copy()

            # 2. Advanced Mathematical Scoring Equations
            # Incorporating Volume Intensity, Open Interest Momentum (Change in OI), 
            # and Volatility Normalization (IV) to eliminate overpriced/dead options.
            # We also add a Moneyness Decay Factor to favor ATM/Near-OTM strikes for jackpot moves.
            
            analysis_df['Moneyness_Weight'] = 1.0 / (1.0 + 0.1 * abs(analysis_df['Strike'] - spot_price) / 100)

            # Call Mathematical Score Equation
            analysis_df['Call_Math_Score'] = (
                (analysis_df['Call_Volume'] * 0.45) + 
                (analysis_df['Call_Chng_OI'] * 0.55)
            ) * analysis_df['Moneyness_Weight'] / (analysis_df['Call_IV'] + 1e-5)

            # Put Mathematical Score Equation
            analysis_df['Put_Math_Score'] = (
                (analysis_df['Put_Volume'] * 0.45) + 
                (analysis_df['Put_Chng_OI'] * 0.55)
            ) * analysis_df['Moneyness_Weight'] / (analysis_df['Put_IV'] + 1e-5)

            # 3. Determine Absolute Best Strike & Direction
            max_call_score = analysis_df['Call_Math_Score'].max()
            max_put_score = analysis_df['Put_Math_Score'].max()

            if max_call_score >= max_put_score:
                best_row = analysis_df.loc[analysis_df['Call_Math_Score'].idxmax()]
                strike = int(best_row['Strike'])
                option_type = "CE (CALL)"
                entry_price = float(best_row['Call_LTP'])
                iv = float(best_row['Call_IV'])
                volume = int(best_row['Call_Volume'])
                chng_oi = int(best_row['Call_Chng_OI'])
            else:
                best_row = analysis_df.loc[analysis_df['Put_Math_Score'].idxmax()]
                strike = int(best_row['Strike'])
                option_type = "PE (PUT)"
                entry_price = float(best_row['Put_LTP'])
                iv = float(best_row['Put_IV'])
                volume = int(best_row['Put_Volume'])
                chng_oi = int(best_row['Put_Chng_OI'])

            # Safety check for zero/negative entry prices
            if entry_price <= 0:
                st.warning("The selected strike has zero or invalid LTP. Please check your data source.")
            else:
                # 4. Dynamic Mathematical Target & Risk-Managed Stop Loss
                # Scaling target dynamically based on Implied Volatility (IV expansion capability)
                iv_multiplier = max(1.5, min(2.2, 1.0 + (iv / 50.0)))
                math_target = entry_price * iv_multiplier
                math_stop_loss = entry_price * 0.72  # Strict 28% mathematical risk buffer for options buying

                # Display Dashboard Results
                st.success("Mathematical Optimization Successful!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="🔥 Ultimate Jackpot Strike", value=f"{strike} {option_type}")
                    st.metric(label="💵 Exact Entry Price (LTP)", value=f"₹{entry_price:.2f}")
                with col2:
                    st.metric(label="🎯 Single Mathematical Target", value=f"₹{math_target:.2f}")
                    st.metric(label="🛑 Stop Loss", value=f"₹{math_stop_loss:.2f}")

                st.info(f"📊 Underlying Metrics -> Volume: {volume:,} | Change in OI: {chng_oi:,} | IV: {iv:.2f}")

    except Exception as e:
        st.error(f"Error during mathematical execution: {e}")
else:
    st.info("Please upload your option chain CSV file to begin analysis.")
