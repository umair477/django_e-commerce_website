Technical Specification: Sprint 3 (Updated) - User Experience & Order Depth

Objective: Finalize the localized payment system, fix SMTP email, refactor the Tabbed Dashboard, and implement a high-fidelity "Order Detail" view.

1. Order History & Detail View Implementation

    Goal: Allow users to click a specific order in their history to view a comprehensive breakdown (ref: image.png).

    Backend Requirement:

        Create a OrderDetailView that retrieves a specific Order object using its ID/UUID.

        Security: Implement a UserPassesTestMixin to ensure a user can only view their own orders.

    Frontend Template Requirements:

        Header: Display Order Reference ID (e.g., DBJYYHEAJ), placement date, and a "Reorder" button.

        Summary Section: Display "Carrier" and "Payment Method" (COD, Easypaisa, etc.).

        Status Tracker: A table or list showing the order's status history (e.g., "Awaiting Payment," "Shipped").

        Address Grid: Side-by-side layout for "Delivery Address" and "Invoice Address."

        Itemized Table:

            Columns: Product (Image + Name + Attributes like Size/Reference), Quantity, Unit Price, Total Price.

            Footer: Subtotal, Shipping/Handling, Tax, and Grand Total.