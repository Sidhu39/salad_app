
import streamlit as st
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Fresh Bowl Café - POS System",
    page_icon="🥗",
    layout="wide"
)

# Business data structure
MENU_DATA = {
    "bases": {
        "Green Garden Salad": {"small": 6.90, "medium": 8.90, "large": 10.90},
        "Power Grain Bowl": {"small": 7.90, "medium": 9.90, "large": 12.90},
        "Mediterranean Mix": {"small": 7.50, "medium": 9.50, "large": 11.90},
        "Asian Fusion Bowl": {"small": 8.50, "medium": 10.50, "large": 13.50}
    },
    "regular_toppings": [
        "Cherry Tomatoes", "Cucumber", "Red Onion", "Bell Pepper", 
        "Carrots", "Purple Cabbage", "Corn", "Black Beans", "Chickpeas"
    ],
    "premium_toppings": {
        "Avocado": 2.50,
        "Grilled Chicken": 3.50,
        "Smoked Salmon": 4.50,
        "Feta Cheese": 2.00,
        "Walnuts": 1.50,
        "Sunflower Seeds": 1.00
    },
    "smoothies": {
        "Tropical Paradise": 5.90,
        "Berry Blast": 5.50,
        "Green Goddess": 6.50,
        "Chocolate Protein": 6.90
    }
}

# Tax and charges
GST_RATE = 0.07  # 7% GST
SERVICE_CHARGE_RATE = 0.05  # 5% service charge for dine-in
MEMBER_DISCOUNT_RATE = 0.10  # 10% member discount
COMBO_DISCOUNT = 2.00  # $2 off when buying salad + smoothie

# Initialize session state
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'cart_id_counter' not in st.session_state:
    st.session_state.cart_id_counter = 0

# Helper functions
def calculate_item_price(base, size, regular_toppings, premium_toppings, quantity):
    """Calculate the price for a single salad item"""
    base_price = MENU_DATA["bases"][base][size]

    # First 3 regular toppings are free
    extra_regular_toppings = max(0, len(regular_toppings) - 3)
    regular_topping_cost = extra_regular_toppings * 0.80  # $0.80 per extra regular topping

    # Premium toppings cost extra
    premium_cost = sum(MENU_DATA["premium_toppings"][topping] for topping in premium_toppings)

    item_total = (base_price + regular_topping_cost + premium_cost) * quantity
    return item_total, base_price, regular_topping_cost, premium_cost

def add_to_cart(item_type, name, details, price, quantity):
    """Add item to cart"""
    st.session_state.cart_id_counter += 1
    cart_item = {
        'id': st.session_state.cart_id_counter,
        'type': item_type,
        'name': name,
        'details': details,
        'price': price,
        'quantity': quantity,
        'total': price * quantity
    }
    st.session_state.cart.append(cart_item)

def remove_from_cart(item_id):
    """Remove item from cart"""
    st.session_state.cart = [item for item in st.session_state.cart if item['id'] != item_id]

def calculate_total():
    """Calculate cart total with all discounts and charges"""
    if not st.session_state.cart:
        return 0, 0, 0, 0, 0, 0

    subtotal = sum(item['total'] for item in st.session_state.cart)

    # Check for combo discount
    has_salad = any(item['type'] == 'salad' for item in st.session_state.cart)
    has_smoothie = any(item['type'] == 'smoothie' for item in st.session_state.cart)
    combo_discount = COMBO_DISCOUNT if (has_salad and has_smoothie) else 0

    # Apply member discount
    member_discount = subtotal * MEMBER_DISCOUNT_RATE if st.session_state.get('is_member', False) else 0

    # Calculate after discounts
    after_discounts = subtotal - combo_discount - member_discount

    # Apply service charge (if dine-in)
    service_charge = after_discounts * SERVICE_CHARGE_RATE if st.session_state.get('dine_in', False) else 0

    # Apply GST
    gst = (after_discounts + service_charge) * GST_RATE

    final_total = after_discounts + service_charge + gst

    return subtotal, combo_discount, member_discount, service_charge, gst, final_total

# Main app
def main():
    st.title("🥗 Fresh Bowl Café - Point of Sale System")
    st.markdown("*Build your perfect salad or smoothie - Quick, accurate pricing for busy cashiers*")

    # Sidebar for customer options
    with st.sidebar:
        st.header("📋 Order Options")
        st.session_state.is_member = st.checkbox("💳 Member Customer", value=st.session_state.get('is_member', False))
        st.session_state.dine_in = st.checkbox("🍽️ Dine-in (5% service charge)", value=st.session_state.get('dine_in', False))

        if st.button("🗑️ Clear Cart"):
            st.session_state.cart = []
            st.rerun()

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🛒 Add Items")

        # Tabs for different product categories
        tab1, tab2 = st.tabs(["🥗 Custom Salads", "🥤 Smoothies"])

        with tab1:
            st.subheader("Build Your Salad")

            # Salad configuration
            col_base, col_size = st.columns(2)

            with col_base:
                selected_base = st.selectbox(
                    "Choose your base:",
                    list(MENU_DATA["bases"].keys())
                )

            with col_size:
                selected_size = st.selectbox(
                    "Select size:",
                    ["small", "medium", "large"],
                    index=1  # Default to medium
                )

            # Display base price
            base_price = MENU_DATA["bases"][selected_base][selected_size]
            st.info(f"Base price: ${base_price:.2f} (includes first 3 regular toppings)")

            # Regular toppings
            st.write("**Regular Toppings** (first 3 free, then $0.80 each):")
            selected_regular_toppings = []

            # Create columns for checkboxes
            cols = st.columns(3)
            for i, topping in enumerate(MENU_DATA["regular_toppings"]):
                with cols[i % 3]:
                    if st.checkbox(topping, key=f"regular_{topping}"):
                        selected_regular_toppings.append(topping)

            # Premium toppings
            st.write("**Premium Toppings:**")
            selected_premium_toppings = []

            cols = st.columns(2)
            for i, (topping, price) in enumerate(MENU_DATA["premium_toppings"].items()):
                with cols[i % 2]:
                    if st.checkbox(f"{topping} (+${price:.2f})", key=f"premium_{topping}"):
                        selected_premium_toppings.append(topping)

            # Quantity
            salad_quantity = st.number_input("Quantity:", min_value=1, max_value=10, value=1, key="salad_qty")

            # Calculate price
            if selected_base:
                item_total, base_price, regular_cost, premium_cost = calculate_item_price(
                    selected_base, selected_size, selected_regular_toppings, selected_premium_toppings, salad_quantity
                )

                # Price breakdown
                st.write("**Price Breakdown:**")
                st.write(f"- Base ({selected_size}): ${base_price:.2f}")
                if regular_cost > 0:
                    extra_regular = len(selected_regular_toppings) - 3
                    st.write(f"- Extra regular toppings ({extra_regular}): ${regular_cost:.2f}")
                if premium_cost > 0:
                    st.write(f"- Premium toppings: ${premium_cost:.2f}")
                if salad_quantity > 1:
                    st.write(f"- Quantity: {salad_quantity}")
                st.write(f"**Total: ${item_total:.2f}**")

                # Add to cart button
                if st.button("🛒 Add Salad to Cart", key="add_salad"):
                    details = {
                        'base': selected_base,
                        'size': selected_size,
                        'regular_toppings': selected_regular_toppings,
                        'premium_toppings': selected_premium_toppings
                    }
                    add_to_cart('salad', f"{selected_base} ({selected_size})", details, item_total/salad_quantity, salad_quantity)
                    st.success("Salad added to cart!")
                    st.rerun()

        with tab2:
            st.subheader("Choose Your Smoothie")

            col_smoothie, col_qty = st.columns([2, 1])

            with col_smoothie:
                selected_smoothie = st.selectbox(
                    "Select smoothie:",
                    list(MENU_DATA["smoothies"].keys())
                )

            with col_qty:
                smoothie_quantity = st.number_input("Quantity:", min_value=1, max_value=10, value=1, key="smoothie_qty")

            if selected_smoothie:
                smoothie_price = MENU_DATA["smoothies"][selected_smoothie]
                total_smoothie_price = smoothie_price * smoothie_quantity

                st.info(f"Price: ${smoothie_price:.2f} each")
                if smoothie_quantity > 1:
                    st.write(f"Total: ${total_smoothie_price:.2f}")

                if st.button("🛒 Add Smoothie to Cart", key="add_smoothie"):
                    add_to_cart('smoothie', selected_smoothie, {}, smoothie_price, smoothie_quantity)
                    st.success("Smoothie added to cart!")
                    st.rerun()

    with col2:
        st.header("🧾 Current Order")

        if st.session_state.cart:
            # Display cart items
            for item in st.session_state.cart:
                with st.container():
                    st.write(f"**{item['name']}** (x{item['quantity']})")

                    if item['type'] == 'salad':
                        details = item['details']
                        st.write(f"- Size: {details['size']}")
                        if details['regular_toppings']:
                            st.write(f"- Regular: {', '.join(details['regular_toppings'][:3])}")
                            if len(details['regular_toppings']) > 3:
                                st.write(f"- Extra regular: {', '.join(details['regular_toppings'][3:])}")
                        if details['premium_toppings']:
                            st.write(f"- Premium: {', '.join(details['premium_toppings'])}")

                    col_price, col_remove = st.columns([2, 1])
                    with col_price:
                        st.write(f"${item['total']:.2f}")
                    with col_remove:
                        if st.button("❌", key=f"remove_{item['id']}", help="Remove item"):
                            remove_from_cart(item['id'])
                            st.rerun()

                    st.divider()

            # Calculate totals
            subtotal, combo_discount, member_discount, service_charge, gst, final_total = calculate_total()

            # Display total breakdown
            st.subheader("💰 Total Breakdown")
            st.write(f"Subtotal: ${subtotal:.2f}")

            if combo_discount > 0:
                st.write(f"Combo Discount: -${combo_discount:.2f} 🎉")

            if member_discount > 0:
                st.write(f"Member Discount (10%): -${member_discount:.2f} 💳")

            if service_charge > 0:
                st.write(f"Service Charge (5%): +${service_charge:.2f}")

            st.write(f"GST (7%): +${gst:.2f}")

            st.markdown(f"### **TOTAL: ${final_total:.2f}**")

            # Payment button
            if st.button("💳 Process Payment", key="payment", type="primary"):
                st.balloons()
                st.success(f"Payment of ${final_total:.2f} processed successfully!")

                # Generate receipt
                st.write("**Receipt Generated:**")
                st.write(f"Fresh Bowl Café - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.write("="*30)
                for item in st.session_state.cart:
                    st.write(f"{item['name']} x{item['quantity']} - ${item['total']:.2f}")
                st.write("="*30)
                st.write(f"TOTAL: ${final_total:.2f}")

                # Clear cart after payment
                if st.button("🆕 New Order"):
                    st.session_state.cart = []
                    st.rerun()
        else:
            st.info("Cart is empty. Add some items to get started!")

            # Show sample pricing
            st.subheader("📋 Quick Reference")
            st.write("**Base Prices:**")
            for base, prices in MENU_DATA["bases"].items():
                st.write(f"- {base}: S${prices['small']:.2f} | M${prices['medium']:.2f} | L${prices['large']:.2f}")

            st.write("**Premium Toppings:**")
            for topping, price in MENU_DATA["premium_toppings"].items():
                st.write(f"- {topping}: +${price:.2f}")

    # Footer with business info
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🥗 Fresh Bowl Café | Healthy • Fresh • Fast<br>
    💡 Tips: Get $2 off with salad+smoothie combo | 10% member discount | First 3 regular toppings free
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
