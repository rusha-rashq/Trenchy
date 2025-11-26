# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
import json
import sqlite3
from typing import Any, Dict, List, Optional, Text

import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import ActionExecuted, SessionStarted, SlotSet
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict


def log_analytics_event(event_type: Text, order_id: Optional[Text] = None):
    """Logs a successful bot event to the analytics table."""
    try:
        # Connects to the same database
        conn = sqlite3.connect("orders.db")
        c = conn.cursor()

        # Inserts the new event record
        c.execute(
            "INSERT INTO analytics_log (event_type, order_id) VALUES (?, ?)",
            (event_type, order_id),
        )

        conn.commit()
        conn.close()
        print(f"ANALYTICS: Logged event '{event_type}' for order '{order_id}'")
    except Exception as e:
        print(f"ANALYTICS ERROR: Failed to log event. {e}")


class ActionGetOrderStatus(Action):
    def name(self) -> Text:
        return "action_get_order_status"

    def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message(text="Zaroor! Kripya apna order ID bataiye.")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute(
            "SELECT status, estimated_delivery FROM orders WHERE id=?", (order_id,)
        )
        order_result = c.fetchone()
        conn.close()

        slot_to_set = [SlotSet("order_id", None)]

        if order_result:
            status, date = order_result[0], order_result[1]
            status_msg = f"Aapke order ID {order_id} ka status hai: '{status}'. Ye {date} tak pahunch jayega."
            dispatcher.utter_message(text=status_msg)

            if status.lower() == "delivered":
                slot_to_set = [
                    SlotSet("order_id", None),
                    SlotSet("upsell_opportunity", True),
                ]

        else:
            response = (
                f"Maaf kijiye, mujhe aapka order ID {order_id} database mein nahi mila."
            )
            dispatcher.utter_message(text=response)

        return slot_to_set


class ActionCancelOrder(Action):
    def name(self) -> Text:
        return "action_cancel_order"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Get the order_id
        order_id = next(tracker.get_latest_entity_values("order_id"), None)

        # If no order_id was found, ask for it.
        if not order_id:
            dispatcher.utter_message(
                text="Theek hai, kripya apna order ID bataiye jise aap cancel karna chahte hain."
            )
            return []

        try:
            conn = sqlite3.connect("orders.db")
            c = conn.cursor()

            # First, check the status
            c.execute("SELECT status FROM orders WHERE id=?", (order_id,))
            result = c.fetchone()

            if not result:
                response_text = f"Maaf kijiye, mujhe aapka order ID {order_id} database mein nahi mila."
            else:
                status = result[0]
                if status == "Processing":
                    # It's processing, so we can cancel it.
                    # We will UPDATE the status to 'Cancelled'
                    c.execute(
                        "UPDATE orders SET status='Cancelled' WHERE id=?", (order_id,)
                    )
                    conn.commit()
                    response_text = f"Aapka order {order_id} safaltapoorvak cancel kar diya gaya hai."

                    log_analytics_event("successful_cancellation", order_id)
                else:
                    # It's already 'Shipped' or 'Delivered'
                    response_text = f"Maaf kijiye, aapka order {order_id} pehle hi '{status}' ho chuka hai, ise cancel nahi kiya ja sakta."

            conn.close()
            dispatcher.utter_message(text=response_text)

        except Exception as e:
            print(f"Database error: {e}")
            dispatcher.utter_message(
                text="Maaf kijiye, database se connect karne mein kuch problem aa rahi hai."
            )

        return [SlotSet("order_id", None)]


class ActionReinstateOrder(Action):
    def name(self) -> Text:
        return "action_reinstate_order"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = next(tracker.get_latest_entity_values("order_id"), None)

        if not order_id:
            dispatcher.utter_message(
                text="Theek hai, kripya apna order ID bataiye jise aap reinstate karna chahte hain."
            )
            return []

        try:
            conn = sqlite3.connect("orders.db")
            c = conn.cursor()
            c.execute("SELECT status FROM orders WHERE id=?", (order_id,))
            result = c.fetchone()

            if not result:
                response_text = f"Maaf kijiye, mujhe aapka order ID {order_id} database mein nahi mila."
            else:
                status = result[0]
                if status == "Cancelled":
                    # Set it back to 'Processing'
                    c.execute(
                        "UPDATE orders SET status='Processing' WHERE id=?", (order_id,)
                    )
                    conn.commit()
                    response_text = f"Aapka order {order_id} safaltapoorvak reinstate kar diya gaya hai. Ye ab 'Processing' mein hai."
                else:
                    response_text = f"Aapka order {order_id} abhi '{status}' hai, ise reinstate nahi kiya ja sakta."

            conn.close()
            dispatcher.utter_message(text=response_text)

        except Exception as e:
            print(f"Database error: {e}")
            dispatcher.utter_message(
                text="Maaf kijiye, database se connect karne mein kuch problem aa rahi hai."
            )

        return []


class ActionChangeAddress(Action):
    def name(self) -> Text:
        return "action_change_address"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")
        new_address = tracker.get_slot("new_address")  # Get address from slot

        if not order_id:
            dispatcher.utter_message(response="utter_ask_order_id_for_address")
            return []
        if not new_address:
            dispatcher.utter_message(response="utter_ask_new_address")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()

        # First, check if order is already shipped
        c.execute("SELECT status FROM orders WHERE id=?", (order_id,))
        result = c.fetchone()

        if result and result[0] in ("Shipped", "Delivered"):
            dispatcher.utter_message(response="utter_address_change_fail")
        elif result:
            # Order is not shipped, so update the address
            c.execute(
                "UPDATE orders SET address = ? WHERE id = ?", (new_address, order_id)
            )
            conn.commit()
            dispatcher.utter_message(response="utter_address_change_confirm")
        else:
            response = (
                f"Maaf kijiye, mujhe aapka order ID {order_id} database mein nahi mila."
            )
            dispatcher.utter_message(text=response)

        conn.close()
        return [SlotSet("order_id", None), SlotSet("new_address", None)]


class ActionExpediteShipping(Action):
    def name(self) -> Text:
        return "action_expedite_shipping"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")

        if not order_id:
            dispatcher.utter_message(response="utter_ask_order_id_for_expedite")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute("SELECT status FROM orders WHERE id=?", (order_id,))
        result = c.fetchone()

        if result and result[0] in ("Shipped", "Delivered"):
            dispatcher.utter_message(response="utter_expedite_fail")
        elif result:
            dispatcher.utter_message(response="utter_expedite_confirm")
        else:
            response = (
                f"Maaf kijiye, mujhe aapka order ID {order_id} database mein nahi mila."
            )
            dispatcher.utter_message(text=response)

        conn.close()
        return [SlotSet("order_id", None)]


class ActionGetInvoice(Action):
    def name(self) -> Text:
        return "action_get_invoice"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")

        if not order_id:
            dispatcher.utter_message(response="utter_ask_order_id_for_invoice")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        # Assuming you have an 'email' column in your 'orders' table
        c.execute("SELECT email FROM orders WHERE id=?", (order_id,))
        result = c.fetchone()

        if result:
            # In a real system, you would use an email API (like SendGrid)
            # For our prototype, we just confirm it.
            # user_email = result[0]
            # print(f"Faking email send of invoice for {order_id} to {user_email}")
            dispatcher.utter_message(response="utter_invoice_confirm")
        else:
            response = (
                f"Maaf kijiye, mujhe aapka order ID {order_id} database mein nahi mila."
            )
            dispatcher.utter_message(text=response)

        conn.close()
        return [SlotSet("order_id", None)]


class ActionChangeOrderDetails(Action):
    def name(self) -> Text:
        return "action_change_order_details"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # It's best to hand this off to a human agent.
        dispatcher.utter_message(response="utter_change_order_not_possible")
        return []


class ActionGetRefundStatus(Action):
    def name(self) -> Text:
        return "action_get_refund_status"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message(response="utter_ask_order_id_for_refund_status")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute("SELECT status FROM returns WHERE order_id=?", (order_id,))
        result = c.fetchone()
        conn.close()

        if result:
            status = result[0]
            dispatcher.utter_message(
                response="utter_refund_status_msg", order_id=order_id, status=status
            )
        else:
            dispatcher.utter_message(
                response="utter_no_refund_found", order_id=order_id
            )

        return [SlotSet("order_id", None)]


class ActionInitiateReturn(Action):
    def name(self) -> Text:
        return "action_initiate_return"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message(response="utter_ask_order_id_for_return")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()

        # Check if a return is already pending
        c.execute("SELECT status FROM returns WHERE order_id=?", (order_id,))
        result = c.fetchone()

        if result:
            dispatcher.utter_message(
                response="utter_already_processing_return",
                order_id=order_id,
                status=result[0],
            )
        else:
            # No pending return, so create a new one
            c.execute(
                "INSERT INTO returns (order_id, reason, status) VALUES (?, ?, ?)",
                (order_id, "user_return", "Pending Pickup"),
            )
            conn.commit()
            dispatcher.utter_message(response="utter_return_confirm", order_id=order_id)
            log_analytics_event("successful_return_request", order_id)

        conn.close()
        return [SlotSet("order_id", None)]


class ActionInitiateExchange(Action):
    def name(self) -> Text:
        return "action_initiate_exchange"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message(response="utter_ask_order_id_for_exchange")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()

        c.execute("SELECT status FROM returns WHERE order_id=?", (order_id,))
        result = c.fetchone()

        if result:
            dispatcher.utter_message(
                response="utter_already_processing_return",
                order_id=order_id,
                status=result[0],
            )
        else:
            c.execute(
                "INSERT INTO returns (order_id, reason, status) VALUES (?, ?, ?)",
                (order_id, "user_exchange", "Pending Pickup"),
            )
            conn.commit()
            dispatcher.utter_message(
                response="utter_exchange_confirm", order_id=order_id
            )

        conn.close()
        return [SlotSet("order_id", None)]


class ActionReportDamagedItem(Action):
    def name(self) -> Text:
        return "action_report_damaged_item"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message(response="utter_ask_order_id_for_damaged")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()

        c.execute("SELECT status FROM returns WHERE order_id=?", (order_id,))
        result = c.fetchone()

        if result:
            dispatcher.utter_message(
                response="utter_already_processing_return",
                order_id=order_id,
                status=result[0],
            )
        else:
            c.execute(
                "INSERT INTO returns (order_id, reason, status) VALUES (?, ?, ?)",
                (order_id, "damaged_item", "Investigating"),
            )
            conn.commit()
            dispatcher.utter_message(
                response="utter_damaged_report_confirm", order_id=order_id
            )

        conn.close()
        return [SlotSet("order_id", None)]


class ActionReportMissingItem(Action):
    def name(self) -> Text:
        return "action_report_missing_item"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        order_id = tracker.get_slot("order_id")
        if not order_id:
            dispatcher.utter_message(response="utter_ask_order_id_for_missing")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()

        c.execute("SELECT status FROM returns WHERE order_id=?", (order_id,))
        result = c.fetchone()

        if result:
            dispatcher.utter_message(
                response="utter_already_processing_return",
                order_id=order_id,
                status=result[0],
            )
        else:
            c.execute(
                "INSERT INTO returns (order_id, reason, status) VALUES (?, ?, ?)",
                (order_id, "missing_item", "Investigating"),
            )
            conn.commit()
            dispatcher.utter_message(
                response="utter_missing_report_confirm", order_id=order_id
            )

        conn.close()
        return [SlotSet("order_id", None)]


class ActionCheckStock(Action):
    def name(self) -> Text:
        return "action_check_stock"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        product_name = tracker.get_slot("product_name")

        # --- THIS IS THE NEW LOGIC ---
        if not product_name:
            dispatcher.utter_message(response="utter_ask_product_name_for_stock")
            return []
        # --- END OF NEW LOGIC ---

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute(
            "SELECT name, stock_level FROM products WHERE name LIKE ?",
            ("%" + product_name + "%",),
        )
        result = c.fetchone()
        conn.close()

        if result:
            name, stock = result[0], result[1]
            if stock > 0:
                dispatcher.utter_message(
                    response="utter_item_in_stock", product_name=name
                )
            else:
                dispatcher.utter_message(
                    response="utter_item_out_of_stock", product_name=name
                )
        else:
            dispatcher.utter_message(
                response="utter_product_not_found", product_name=product_name
            )

        return [SlotSet("product_name", None)]


class ActionGetProductDetails(Action):
    def name(self) -> Text:
        return "action_get_product_details"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        product_name = tracker.get_slot("product_name")

        if not product_name:
            dispatcher.utter_message(response="utter_ask_product_name_for_details")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute(
            "SELECT name, description, price FROM products WHERE name LIKE ?",
            ("%" + product_name + "%",),
        )
        result = c.fetchone()
        conn.close()

        if result:
            name, desc, price = result[0], result[1], result[2]
            dispatcher.utter_message(
                response="utter_product_details",
                product_name=name,
                description=desc,
                price=price,
            )
        else:
            dispatcher.utter_message(
                response="utter_product_not_found", product_name=product_name
            )

        return [SlotSet("product_name", None)]


class ActionGetRecommendation(Action):
    def name(self) -> Text:
        return "action_get_recommendation"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        price_limit = tracker.get_slot("price_limit")
        if not price_limit:
            dispatcher.utter_message(response="utter_ask_price_range")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()

        c.execute(
            "SELECT name, price FROM products WHERE price <= ? ORDER BY popularity DESC LIMIT 1",
            (price_limit,),
        )
        result = c.fetchone()
        conn.close()

        if result:
            name, price = result[0], result[1]
            dispatcher.utter_message(
                response="utter_recommend_product", product_name=name, price=price
            )
        else:
            dispatcher.utter_message(response="utter_no_recommendation_found")

        return [SlotSet("price_limit", None)]


class ActionApplyDiscount(Action):
    def name(self) -> Text:
        return "action_apply_discount"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        discount_code = tracker.get_slot("discount_code")

        # --- THIS IS THE NEW LOGIC ---
        if not discount_code:
            dispatcher.utter_message(response="utter_ask_discount_code")
            return []
        # --- END OF NEW LOGIC ---

        cart_total = 1000.0

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute(
            "SELECT discount_percent, min_purchase FROM discounts WHERE code = ?",
            (discount_code.upper(),),
        )
        result = c.fetchone()
        conn.close()

        if result:
            percent, min_purchase = result[0], result[1]
            if cart_total >= min_purchase:
                dispatcher.utter_message(
                    response="utter_discount_applied",
                    discount_code=discount_code.upper(),
                    percent=percent,
                )
            else:
                dispatcher.utter_message(
                    response="utter_discount_invalid",
                    discount_code=discount_code.upper(),
                    min_purchase=min_purchase,
                )
        else:
            dispatcher.utter_message(
                response="utter_discount_invalid",
                discount_code=discount_code.upper(),
                min_purchase="N/A",
            )

        return [SlotSet("discount_code", None)]


class ActionCheckLoyaltyPoints(Action):
    def name(self) -> Text:
        return "action_check_loyalty_points"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        email = tracker.get_slot("email_address")
        if not email:
            dispatcher.utter_message(response="utter_ask_email")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute("SELECT loyalty_points FROM users WHERE email=?", (email,))
        result = c.fetchone()
        conn.close()

        if result:
            points = result[0]
            dispatcher.utter_message(
                response="utter_loyalty_points", loyalty_points=points
            )
        else:
            dispatcher.utter_message(response="utter_account_not_found")

        return [SlotSet("email_address", None)]  # Clear the slot


class ActionResetPassword(Action):
    def name(self) -> Text:
        return "action_reset_password"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        email = tracker.get_slot("email_address")
        if not email:
            dispatcher.utter_message(response="utter_ask_email")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute("SELECT 1 FROM users WHERE email=?", (email,))
        result = c.fetchone()
        conn.close()

        if result:
            # In a real app, you would generate a token and send an email
            # Here, we just confirm.
            dispatcher.utter_message(
                response="utter_reset_password_link_sent", email_address=email
            )
        else:
            dispatcher.utter_message(response="utter_account_not_found")

        return [SlotSet("email_address", None)]


class ActionUpdateProfile(Action):
    def name(self) -> Text:
        return "action_update_profile"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        email = tracker.get_slot("email_address")
        phone = tracker.get_slot("phone_number")

        if not email:
            dispatcher.utter_message(response="utter_ask_email")
            return []

        if not phone:
            dispatcher.utter_message(response="utter_ask_new_phone_number")
            return []

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        # First check if user exists
        c.execute("SELECT 1 FROM users WHERE email=?", (email,))
        result = c.fetchone()

        if result:
            # User exists, so update their phone
            c.execute("UPDATE users SET phone = ? WHERE email = ?", (phone, email))
            conn.commit()
            dispatcher.utter_message(response="utter_profile_updated")
        else:
            dispatcher.utter_message(response="utter_account_not_found")

        conn.close()
        return [SlotSet("email_address", None), SlotSet("phone_number", None)]


class ActionResetSentimentSlot(Action):
    """Resets the 'sentiment' slot to None"""

    def name(self) -> Text:
        return "action_reset_sentiment_slot"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        log_analytics_event("angry_customer_handoff")
        return [SlotSet("sentiment", None)]


class ActionProactiveUpsell(Action):
    """Fetches a popular item and offers it to the user, then resets the flag."""

    def name(self) -> Text:
        return "action_proactive_upsell"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        conn = sqlite3.connect("orders.db")
        c = conn.cursor()
        c.execute("SELECT name FROM products ORDER BY popularity DESC LIMIT 1")
        result = c.fetchone()
        conn.close()

        product_name = "new Laptop"  # Default fallback
        if result:
            product_name = result[0]

        upsell_msg = (
            f"Great! By the way, hamara sabse popular item, the '{product_name}', "
            "abhi stock mein hai. Kya aap iske baare mein jaanna chahenge?"
        )
        dispatcher.utter_message(text=upsell_msg)

        # Reset the flag so we don't ask again
        return [SlotSet("upsell_opportunity", None)]


class ActionResetUpsellSlot(Action):
    """Resets the upsell opportunity flag if the user doesn't say thanks."""

    def name(self) -> Text:
        return "action_reset_upsell_slot"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Just reset the slot and do nothing else
        return [SlotSet("upsell_opportunity", None)]


class ActionStoreMetadata(Action):
    def name(self):
        return "action_store_metadata"

    def run(self, dispatcher, tracker, domain):
        product_id = tracker.get_slot("product_id")
        if product_id:
            return [SlotSet("current_product", product_id)]
        return []


BACKEND_URL = "http://localhost:8000"


class ActionAnswerProductQuestion(Action):
    def name(self) -> Text:
        return "action_answer_product_question"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict
    ) -> List[Dict[Text, Any]]:
        print("\n" + "=" * 60)
        print("🔍 DEBUGGING PRODUCT QUESTION ACTION")

        # --- 0. DEBUG: INSPECT RAW MESSAGE (KEPT EXACTLY THE SAME) ---
        try:
            print("🕵️‍♂️ RAW MESSAGE DUMP:")
            print(json.dumps(tracker.latest_message, indent=2))
        except Exception:
            pass

        # --- 1. TRY SLOT FIRST (KEPT EXACTLY THE SAME) ---
        product_id = tracker.get_slot("current_product") or tracker.get_slot(
            "product_id"
        )

        # --- 2. TRY METADATA (KEPT EXACTLY THE SAME) ---
        if not product_id:
            latest_message = tracker.latest_message
            metadata = latest_message.get("metadata", {}) or {}

            product_id = metadata.get("product_id")

            if not product_id and "customData" in metadata:
                product_id = metadata["customData"].get("product_id")

            if not product_id:
                page_url = metadata.get("page_url") or metadata.get("url") or ""
                if "id=" in page_url:
                    try:
                        product_id = page_url.split("id=")[-1].split("&")[0]
                    except Exception:
                        pass

        # --- 3. DEEP SEARCH (KEPT EXACTLY THE SAME) ---
        if not product_id:
            print("🕵️‍♂️ Slot/Metadata empty. Searching session history...")
            for event in tracker.events:
                if event.get("event") == "session_started":
                    metadata = event.get("metadata", {})
                    if "product_id" in metadata:
                        product_id = metadata["product_id"]
                        print(f"✅ Found ID in session_started metadata: {product_id}")
                        break
                    if "customData" in metadata:
                        product_id = metadata["customData"].get("product_id")
                        if product_id:
                            print(
                                f"✅ Found ID in session_started customData: {product_id}"
                            )
                            break

        print(f"✅ FINAL PRODUCT ID FOUND: {product_id}")
        print("=" * 60)

        if not product_id:
            dispatcher.utter_message(
                text="I'm not sure which product you are looking at. Could you tell me the name?"
            )
            return []

        # Save the context
        events = [SlotSet("current_product", product_id)]

        # --- 4. FETCH PRODUCT DATA (MODIFIED TO EXTRACT DETAILS) ---
        try:
            product_res = requests.get(f"{BACKEND_URL}/products/{product_id}")

            if product_res.status_code != 200:
                dispatcher.utter_message(
                    text=f"I found ID {product_id}, but the database returned {product_res.status_code}."
                )
                return events

            product = product_res.json()

            # <--- NEW: Extract explicit details right here --->
            p_name = product.get("name", "Product")
            p_desc = product.get("description", "No description available.")
            p_price = product.get("price", "N/A")

        except Exception as e:
            print(f"❌ API ERROR: {e}")
            dispatcher.utter_message(
                text="I can't connect to the product database right now."
            )
            return events

        # --- 5. GET SEMANTIC ANSWER (MODIFIED WITH FALLBACK) ---
        question = tracker.latest_message.get("text")
        ai_answer = None

        try:
            ans_res = requests.post(
                f"{BACKEND_URL}/semantic_answer",
                json={"question": question, "product": product},
            )
            data = ans_res.json()
            print(f"📦 RAW BACKEND JSON: {data}")

            ai_answer = (
                data.get("answer")
                or data.get("reply")
                or data.get("response")
                or data.get("generated_text")
                or data.get("text")
            )
        except Exception as e:
            print(f"❌ SEMANTIC ERROR: {e}")
            # Don't fail yet! We still have the manual description below.

        # --- 6. FINAL DECISION LOGIC (NEW) ---
        # Check if AI answer is vague or empty
        bad_phrases = [
            "not fully sure",
            "couldn't find",
            "no information",
            "I don't know",
        ]

        is_bad_answer = False
        if not ai_answer:
            is_bad_answer = True
        elif any(phrase in ai_answer for phrase in bad_phrases):
            is_bad_answer = True

        if is_bad_answer:
            print("🤖 AI was vague. Using Database Description + Price instead.")
            final_response = f"**{p_name}**\n{p_desc}\n\n**Price:** ₹{p_price}"
        else:
            print("🤖 AI answer was good.")
            final_response = ai_answer

        dispatcher.utter_message(text=final_response)
        return events


class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    async def run(self, dispatcher, tracker, domain):
        metadata = tracker.get_slot("session_started_metadata") or {}
        print("Session metadata:", metadata)

        events = [SessionStarted()]

        # Send product_id from webchat
        product_id = metadata.get("product_id")
        if product_id:
            events.append(SlotSet("current_product", product_id))
            print("Setting current_product:", product_id)

        # Send page_url too
        url = metadata.get("page_url")
        if url:
            events.append(SlotSet("page_url", url))

        events.append(ActionExecuted("action_listen"))
        return events


class ActionSetProduct(Action):
    """Silently sets the current product context"""

    def name(self) -> Text:
        return "action_set_product"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Try to get product_id from entity
        product_id = next(tracker.get_latest_entity_values("product_id"), None)

        # Also try from slot
        if not product_id:
            product_id = tracker.get_slot("product_id")

        print(f"🎯 ActionSetProduct: Setting product to {product_id}")

        if product_id:
            # Set the current_product slot silently (no message to user)
            return [SlotSet("current_product", product_id)]

        return []


class ActionSetProductExternal(Action):
    """Sets product context from external trigger"""

    def name(self) -> Text:
        return "action_set_product_external"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Get product_id from the trigger event
        product_id = None

        # Check the latest event
        events = tracker.events
        for event in reversed(events):
            if event.get("event") == "user":
                entities = event.get("parse_data", {}).get("entities", [])
                for entity in entities:
                    if entity.get("entity") == "product_id":
                        product_id = entity.get("value")
                        break
                if product_id:
                    break

        print(f"🎯 EXTERNAL TRIGGER: Setting product to {product_id}")

        if product_id:
            return [SlotSet("current_product", product_id)]

        return []
