import streamlit as st
import pandas as pd
from itertools import combinations_with_replacement
from collections import Counter

# Predefined cut lengths
CUT_LENGTHS = [515, 1025, 1145, 1835, 2045, 2075, 2165, 2515, 2835, 3575, 3695, 3755, 3815, 4085, 4155, 4225, 5015, 5375, 5515, 6000]

def find_all_cuts(raw_length, desired_cuts):
    """
    Find all valid cutting combinations based on desired cuts and quantities
    """
    results = []
    
    # Generate all possible combinations
    available_lengths = [length for length, qty in desired_cuts.items() if qty > 0]
    
    if not available_lengths:
        return results
    
    # Try different combination sizes - removed the limit of 6
    max_pieces = sum(desired_cuts.values())  # Maximum possible pieces based on quantities
    for combo_size in range(1, max_pieces + 1):
        for combo in combinations_with_replacement(available_lengths, combo_size):
            total_length = sum(combo)
            
            # Only check if it fits within raw length (removed max_waste constraint)
            if total_length <= raw_length:
                # Check if we have enough quantity for this combination
                combo_count = Counter(combo)
                valid = True
                for length, needed in combo_count.items():
                    if needed > desired_cuts[length]:
                        valid = False
                        break
                
                if valid:
                    waste = raw_length - total_length
                    efficiency = (total_length / raw_length) * 100
                    results.append({
                        'combination': combo,
                        'total_length': total_length,
                        'waste': waste,
                        'efficiency': efficiency,
                        'pieces': len(combo)
                    })
    
    # Sort by efficiency (descending) and then by waste (ascending)
    results.sort(key=lambda x: (-x['efficiency'], x['waste']))
    return results[:5]  # Return only top 5 results

def suggest_optimal_quantities(raw_length):
    """
    Suggest optimal quantities for cut lengths to maximize efficiency
    """
    best_combo = None
    best_efficiency = 0
    
    # Try combinations of 2-4 different lengths
    for combo_size in range(2, 5):
        for combo in combinations_with_replacement(CUT_LENGTHS, combo_size):
            total_length = sum(combo)
            if total_length <= raw_length:
                efficiency = (total_length / raw_length) * 100
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    best_combo = combo
    
    # Convert to quantities dictionary
    suggested_cuts = {length: 0 for length in CUT_LENGTHS}
    if best_combo:
        combo_count = Counter(best_combo)
        for length, count in combo_count.items():
            suggested_cuts[length] = count
    
    return suggested_cuts

def main():
    st.title("🔧 6000mm Article Cutting Optimizer")
    st.write("Find the best cutting combinations for your selected lengths.")
    
    # Input for raw length only
    raw_length = st.number_input(
        "Raw Article Length (mm)", 
        min_value=100, 
        max_value=10000, 
        value=6000, 
        step=1
    )
    
    st.write("---")
    
    # Add suggest button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📏 Select Desired Cut Lengths and Quantities")
    with col2:
        if st.button("🎯 Suggest Optimal Combinations", type="primary"):
            suggested = suggest_optimal_quantities(raw_length)
            st.session_state.update({f"qty_{length}": qty for length, qty in suggested.items()})
            st.rerun()
    
    # Create a grid for cut length selection
    desired_cuts = {}
    
    # Display cut lengths in a grid format
    cols_per_row = 4
    for i in range(0, len(CUT_LENGTHS), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, length in enumerate(CUT_LENGTHS[i:i+cols_per_row]):
            with cols[j]:
                # Use session state for suggested values
                default_value = st.session_state.get(f"qty_{length}", 0)
                qty = st.number_input(
                    f"{length}mm", 
                    min_value=0, 
                    max_value=20,
                    value=default_value, 
                    step=1,
                    key=f"qty_{length}"
                )
                desired_cuts[length] = qty
    
    st.write("---")
    
    # Calculate and display results
    if any(qty > 0 for qty in desired_cuts.values()):
        st.subheader("🎯 Top 5 Cutting Combinations")
        
        results = find_all_cuts(raw_length, desired_cuts)
        
        if results:
            # Display summary
            selected_lengths = [f"{length}mm (×{qty})" for length, qty in desired_cuts.items() if qty > 0]
            st.info(f"**Selected lengths:** {', '.join(selected_lengths)}")
            
            # Create results dataframe
            df_data = []
            for i, result in enumerate(results, 1):
                combo_str = ' + '.join([f"{length}mm" for length in result['combination']])
                df_data.append({
                    'Rank': i,
                    'Combination': combo_str,
                    'Pieces': result['pieces'],
                    'Total Length': f"{result['total_length']}mm",
                    'Waste': f"{result['waste']}mm",
                    'Efficiency': f"{result['efficiency']:.1f}%"
                })
            
            df = pd.DataFrame(df_data)
            
            # Display results table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
            
            # Highlight best option
            if results:
                best = results[0]
                st.success(
                    f"**🏆 Recommended:** {' + '.join([f'{l}mm' for l in best['combination']])} "
                    f"= {best['total_length']}mm (Waste: {best['waste']}mm, Efficiency: {best['efficiency']:.1f}%)"
                )
        else:
            st.warning("No valid combinations found. Make sure the selected lengths can fit within the raw material length.")
    else:
        st.info("👆 Please select cut lengths with quantities > 0, or click 'Suggest Optimal Combinations' to get started.")
        
        # Show available lengths as reference
        st.subheader("📋 Available Cut Lengths")
        lengths_text = ", ".join([f"{length}mm" for length in CUT_LENGTHS])
        st.text(lengths_text)

if __name__ == "__main__":
    main()