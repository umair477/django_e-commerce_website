Technical Specification: Sprint 2 - Localization & UI Refinement

Project Status: Phase 1 (Core Store) complete.

Objective: Implement Pakistani-specific payment gateways, enhance AJAX cart interactivity, add User-Generated Content (Reviews), and refactor the Customer Dashboard UI.

1. Payment Gateway Refactor (Pakistan Localization)

    Deprecation: Remove all PayPal SDK integrations and buttons.

    New Payment Logic: Implement a PaymentMethod selection in the Checkout view with the following logic:

        COD (Cash on Delivery): Create an order with status='Pending' and payment_status='Unpaid'.

        Easypaisa / JazzCash: * Initial Integration: Implement "Mobile Account" fields (Phone Number) in the checkout form.

            Integration Level: If using a 3rd party aggregator (like Foree, Safepay, or direct Merchant APIs), implement the corresponding Redirect/IPN (Instant Payment Notification) logic.

            Fallback: If no API is provided, implement a "Manual Upload" field for transaction ID/Screenshot for admin verification.

2. Enhanced AJAX Cart Modal

    Backend Requirement: Update the add_to_cart view to return a JsonResponse containing:

        product_name, product_price, quantity_added, cart_total_price, and image_url.

    Frontend Requirement: * Replace simple alert/toast with a Bootstrap/Tailwind Modal.

        Trigger: On success of the Fetch/AJAX call, populate the modal fields dynamically using JavaScript and call .show() on the modal.

        CTA Buttons: Include "Continue Shopping" (Close modal) and "View Cart/Checkout" (Redirect).

3. Product Review System

    Data Model: Create a ProductReview model:

        product (FK), user (FK), rating (Integer 1-5), review_text (TextField), created_at (DateTimeField).

    Frontend Logic:

        Display existing reviews on the product_detail.html page.

        Conditional Rendering: Only display the "Write a Review" form if user.is_authenticated.

        Validation: Ensure a user can only review a product once (unique_together constraint on user and product).

4. Dashboard Refactoring (Tabbed Interface)

    Architecture: Move away from a single-scroll page to a Vertical Tabbed Navigation.

    Implementation Options:

        Option A (Django Sub-routing): Use clean URLs (e.g., /account/orders/, /account/profile/) where each tab is a separate view or a view with a URL parameter. (Recommended for SEO and deep-linking).

        Option B (JavaScript/CSS Tabs): Load all content hidden and toggle visibility using classes (e.g., hidden vs block) based on the sidebar click.

    Required Tabs:

        Dashboard Overview: Recent orders and welcome message.

        Order History: Table format with "View Invoice" links.

        Address Book: CRUD functionality for Shipping/Billing addresses.

        Profile Settings: Update name, email, and password.

5. Technical Constraints

    State Management: Ensure the Sidebar "Active" state persists on page refresh.

    Security: Ensure that only the owner of the account can access their specific dashboard views via UserPassesTestMixin or login_required.

    Responsive Design: Ensure the vertical sidebar collapses into a horizontal menu or "Hamburger" icon on mobile devices.