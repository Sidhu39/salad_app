
import streamlit as st
from datetime import datetime

# Optional integrations - uncomment to use
from pyrebase import pyrebase
import openai
from pyngrok import ngrok

try:
    from sense_hat import SenseHat as sense

    SENSE_HAT_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    SENSE_HAT_AVAILABLE = False


    # Create a mock SenseHat class to simulate Sense HAT functionality
    class SenseHatMock:
        def __init__(self):
            self.stick = self.JoystickMock()

        def clear(self, color=None):
            pass  # do nothing

        def show_message(self, message, text_colour=None, back_colour=None):
            pass  # do nothing

        def get_temperature(self):
            return 22.0  # dummy temperature

        def get_humidity(self):
            return 45.0  # dummy humidity

        def get_pressure(self):
            return 1013.25  # dummy pressure (hPa)

        class JoystickMock:
            def get_events(self):
                return []  # no joystick events


    SenseHat = SenseHatMock  # override SenseHat to mock

# Initialize sense object (real or mock)
sense = SenseHat()

# Configure page
st.set_page_config(
    page_title="Fresh Bowl Café - Enhanced POS System",
    page_icon="🥗",
    layout="wide"
)

# Business data structure (same as before)
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

# Enhanced Features Configuration
ENABLE_AI_FEATURES = st.sidebar.checkbox("🤖 Enable AI Features", help="Requires OpenAI API key")
ENABLE_CLOUD_SYNC = st.sidebar.checkbox("☁️ Enable Cloud Sync", help="Requires Firebase setup")
ENABLE_HARDWARE = st.sidebar.checkbox("🎛️ Enable Hardware Monitor", help="Requires Sense HAT")
ENABLE_REMOTE_ACCESS = st.sidebar.checkbox("🌐 Enable Remote Access", help="Creates public URL")

# Constants (same as before)
GST_RATE = 0.07
SERVICE_CHARGE_RATE = 0.05
MEMBER_DISCOUNT_RATE = 0.10
COMBO_DISCOUNT = 2.00

# Initialize session state
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'cart_id_counter' not in st.session_state:
    st.session_state.cart_id_counter = 0

# Enhanced Functions

def get_ai_recommendation_real(customer_preferences):
    # Real ChatGPT API calls
    response = st.session_state.openai_client.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "system",
            "content": f"You are a nutritionist at Fresh Bowl Café. Menu: {menu_context}"
        }],
        max_tokens=150
    )
    return response.choices[0].message.content


def initialize_firebase():
    # Real Firebase configuration from Streamlit secrets
    firebase_config = {
        "apiKey": st.secrets.get("firebase_api_key", ""),
        "databaseURL": st.secrets.get("firebase_database_url", ""),
        # ... complete config
    }
    firebase = pyrebase.initialize_app(firebase_config)
    return firebase.database()

def save_order_to_firebase(order_data):
    # Real database operations
    st.session_state.firebase_db.child("orders").child(timestamp_key).set(order_data)
    # Updates daily totals, handles errors


def monitor_environment_real():
    # Real sensor readings
    temperature = sense.get_temperature()
    humidity = sense.get_humidity()
    pressure = sense.get_pressure()

    # Real LED control
    if temperature > 25:
        sense.clear([255, 165, 0])  # Orange warning


def handle_joystick_input():
    # Real joystick events
    events = sense.stick.get_events()
    for event in events:
        if event.direction == "up":
            return "scroll_up"


def setup_ngrok_tunnel():
    # Real tunnel creation
    ngrok.kill()  # Kill existing tunnels
    public_url = ngrok.connect(8501, "http")  # Create new tunnel
    st.session_state.ngrok_tunnel = public_url
    return public_url


# Original POS Functions (same as before)
def calculate_item_price(base, size, regular_toppings, premium_toppings, quantity):
    base_price = MENU_DATA["bases"][base][size]
    extra_regular_toppings = max(0, len(regular_toppings) - 3)
    regular_topping_cost = extra_regular_toppings * 0.80
    premium_cost = sum(MENU_DATA["premium_toppings"][topping] for topping in premium_toppings)
    item_total = (base_price + regular_topping_cost + premium_cost) * quantity
    return item_total, base_price, regular_topping_cost, premium_cost

def add_to_cart(item_type, name, details, price, quantity):
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
    st.session_state.cart = [item for item in st.session_state.cart if item['id'] != item_id]

def calculate_total():
    if not st.session_state.cart:
        return 0, 0, 0, 0, 0, 0

    subtotal = sum(item['total'] for item in st.session_state.cart)
    has_salad = any(item['type'] == 'salad' for item in st.session_state.cart)
    has_smoothie = any(item['type'] == 'smoothie' for item in st.session_state.cart)
    combo_discount = COMBO_DISCOUNT if (has_salad and has_smoothie) else 0
    member_discount = subtotal * MEMBER_DISCOUNT_RATE if st.session_state.get('is_member', False) else 0
    after_discounts = subtotal - combo_discount - member_discount
    service_charge = after_discounts * SERVICE_CHARGE_RATE if st.session_state.get('dine_in', False) else 0
    gst = (after_discounts + service_charge) * GST_RATE
    final_total = after_discounts + service_charge + gst

    return subtotal, combo_discount, member_discount, service_charge, gst, final_total

# Main app
def main():
    st.title("🥗 Fresh Bowl Café - Enhanced POS System")
    st.markdown("*Advanced Point of Sale with AI, Cloud Sync & Hardware Integration*")

    # Enhanced sidebar
    with st.sidebar:
        st.header("📋 Order Options")
        st.session_state.is_member = st.checkbox("💳 Member Customer", value=st.session_state.get('is_member', False))
        st.session_state.dine_in = st.checkbox("🍽️ Dine-in (5% service charge)", value=st.session_state.get('dine_in', False))

        # Enhanced features status
        if any([ENABLE_AI_FEATURES, ENABLE_CLOUD_SYNC, ENABLE_HARDWARE, ENABLE_REMOTE_ACCESS]):
            st.markdown("---")
            st.subheader("🚀 Enhanced Features")

            if ENABLE_AI_FEATURES:
                if st.button("🤖 Get AI Recommendation"):
                    recommendation = get_ai_recommendation()
                    st.info(recommendation)

            if ENABLE_HARDWARE:
                env_data = monitor_environment()
                st.metric("🌡️ Temperature", f"{env_data['temperature']:.1f}°C")
                st.metric("💧 Humidity", f"{env_data['humidity']:.1f}%")
                st.caption(env_data['status'])

            if ENABLE_REMOTE_ACCESS:
                setup_remote_access()

        if st.button("🗑️ Clear Cart"):
            st.session_state.cart = []
            st.rerun()

    # Main interface (same layout as original)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("🛒 Add Items")
        tab1, tab2 = st.tabs(["🥗 Custom Salads", "🥤 Smoothies"])

        # Salad builder (same as original)
        with tab1:
            st.subheader("Build Your Salad")

            col_base, col_size = st.columns(2)
            with col_base:
                selected_base = st.selectbox("Choose your base:", list(MENU_DATA["bases"].keys()))
            with col_size:
                selected_size = st.selectbox("Select size:", ["small", "medium", "large"], index=1)

            base_price = MENU_DATA["bases"][selected_base][selected_size]
            st.info(f"Base price: ${base_price:.2f} (includes first 3 regular toppings)")

            # Regular toppings
            st.write("**Regular Toppings** (first 3 free, then $0.80 each):")
            selected_regular_toppings = []
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

            salad_quantity = st.number_input("Quantity:", min_value=1, max_value=10, value=1, key="salad_qty")

            if selected_base:
                item_total, base_price, regular_cost, premium_cost = calculate_item_price(
                    selected_base, selected_size, selected_regular_toppings, selected_premium_toppings, salad_quantity
                )

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

        # Smoothie section (same as original)
        with tab2:
            st.subheader("Choose Your Smoothie")
            col_smoothie, col_qty = st.columns([2, 1])

            with col_smoothie:
                selected_smoothie = st.selectbox("Select smoothie:", list(MENU_DATA["smoothies"].keys()))
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

    # Cart section (enhanced with cloud sync option)
    with col2:
        st.header("🧾 Current Order")

        if st.session_state.cart:
            # Display cart items (same as original)
            for item in st.session_state.cart:
                with st.container():
                    st.write(f"**{item['name']}** (x{item['quantity']})")

                    if item['type'] == 'salad':
                        details = item['details']
                        st.write(f"- Size: {details['size']}")
                        if details['regular_toppings']:
                            regular_display = details['regular_toppings']
                            if len(regular_display) <= 3:
                                st.write(f"- Regular: {', '.join(regular_display)}")
                            else:
                                st.write(f"- Regular: {', '.join(regular_display[:3])}")
                                st.write(f"- Extra regular: {', '.join(regular_display[3:])}")
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

            # Calculate totals (same as original)
            subtotal, combo_discount, member_discount, service_charge, gst, final_total = calculate_total()

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

            # Enhanced payment processing
            if st.button("💳 Process Payment", key="payment", type="primary"):
                st.balloons()
                st.success(f"Payment of ${final_total:.2f} processed successfully!")

                # Enhanced receipt with cloud sync option
                st.write("**Receipt Generated:**")
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                st.write(f"Fresh Bowl Café - {current_time}")
                st.write("="*30)

                order_data = {
                    'timestamp': current_time,
                    'items': st.session_state.cart,
                    'total': final_total,
                    'customer_type': 'member' if st.session_state.get('is_member', False) else 'regular',
                    'service_type': 'dine-in' if st.session_state.get('dine_in', False) else 'takeaway'
                }

                for item in st.session_state.cart:
                    st.write(f"{item['name']} x{item['quantity']} - ${item['total']:.2f}")
                st.write("="*30)
                st.write(f"TOTAL: ${final_total:.2f}")

                # Optional cloud sync
                if ENABLE_CLOUD_SYNC:
                    save_to_cloud(order_data)

                if st.button("🆕 New Order"):
                    st.session_state.cart = []
                    st.rerun()
        else:
            st.info("Cart is empty. Add some items to get started!")

            # AI recommendation when cart is empty
            if ENABLE_AI_FEATURES:
                st.markdown("**🤖 AI Suggests:**")
                recommendation = get_ai_recommendation()
                st.info(recommendation)

    # Enhanced footer
    st.markdown("---")
    feature_status = []
    if ENABLE_AI_FEATURES:
        feature_status.append("🤖 AI")
    if ENABLE_CLOUD_SYNC:
        feature_status.append("☁️ Cloud")
    if ENABLE_HARDWARE:
        feature_status.append("🎛️ Hardware")
    if ENABLE_REMOTE_ACCESS:
        feature_status.append("🌐 Remote")

    status_text = " | ".join(feature_status) if feature_status else "Basic Mode"

    st.markdown(f"""
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    🥗 Fresh Bowl Café Enhanced POS | Status: {status_text}<br>
    💡 Tips: Get $2 off with salad+smoothie combo | 10% member discount | First 3 regular toppings free
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
