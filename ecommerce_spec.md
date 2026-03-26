Technical Specification: Professional Django E-Commerce Platform

1. Project Overview

Objective: Transform a static Django-based e-commerce theme into a fully functional, dynamic, and production-ready platform.
Framework: Django 5.2.4
Primary Database: PostgreSQL
Frontend Strategy: Integrate logic into existing HTML templates located in the project directory.

2. Core Architecture & Models

The Agent must implement/expand the following data structures:

    CustomUser: Extend AbstractUser to include phone_number, profile_image, and preferred_language.

    Product: Include slug (for SEO), stock_count, price, discount_price, is_active, and metadata.

    Category: Hierarchical structure (Parent/Child) with SEO slugs.

    Order & OrderItem: Tracking status (Pending, Paid, Shipped, Delivered), transaction_id, and shipping_address.

    Address: Linked to User for "My Account" management (Billing vs. Shipping).

3. Functional Requirements
    Phase 1: Authentication & Identity (IAM)

        Registration Flow: Custom signup form with email verification.

        Email System: Configure django.core.mail with an SMTP backend. Send a "Welcome" email upon successful registration.

        Password Management: Full implementation of "Forgot Password" using Django’s native auth views with custom-styled email templates.

        Customer Dashboard: A "My Account" view providing:

            Order history with status badges.

            Profile editing and password change.

            Address book management.

    Phase 2: Product Discovery & Internationalization

        Advanced Filtering: Use django-filter to enable filtering by:

            Price Range (Min/Max).

            Attributes (Size, Color, Brand).

            Availability (In Stock only).

        Multilingual Support (i18n):

            Activate LocaleMiddleware.

            Implement URL-based language prefixes (e.g., /en/, /it/).

            Use gettext for all hardcoded UI strings.

        SEO Optimization: Dynamic meta tags, OpenGraph tags, and sitemap generation.

    Phase 3: Cart & Interactive UI

        AJAX Cart: Implement "Add to Cart" functionality without page reload.

        Pop-up Notification: On successful addition, trigger a "Mini-Cart" pop-up or toast notification showing item details.

        Session Persistence: Ensure the cart persists for guest users and merges with the account upon login.

    Phase 4: Checkout & Payments

        Multi-step Checkout: 1. Shipping/Billing Details selection.
        2. Order Review.
        3. Payment Processing.

        Payment Integration: Integrate Stripe or PayPal using their respective Python SDKs.

        Post-Payment Logic: Generate unique Order IDs, decrease inventory levels, and send an automated PDF invoice/receipt via email.

4. Professional "Must-Have" Features

The Agent should implement these additional features for a "Complete Store" experience:

    Coupon/Discount Engine: A model for discount codes with expiration dates and usage limits.

    Wishlist System: Ability for logged-in users to "Heart" items for later purchase.

    Product Reviews: A rating and comment system for verified purchasers.

    Admin Dashboard: Customize django-admin to include a "Sales Overview" and order fulfillment management.

    Image Optimization: Use django-imagekit or similar to generate thumbnails and compressed web versions of product photos.

5. Technical Constraints & Security

    Security: All forms must use {% csrf_token %}. Sensitive data like API keys must be stored in .env files.

    Performance: Implement database indexing on slug, name, and category fields. Use select_related and prefetch_related in QuerySets to avoid N+1 problems.

    Static Files: Ensure all paths in the existing theme are updated to use the {% static %} template tag.

6. Execution Instructions for the Agent

    Analyze the existing template structure in the project directory.

    Initialize the Custom User model before running any migrations.

    Build the backend logic for each phase incrementally, ensuring the frontend templates are updated to display dynamic data using Django Template Language (DTL).

    Test the checkout flow using "Test Mode" API keys for the chosen payment gateway.