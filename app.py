import streamlit as st
import pandas as pd

import database as db


st.set_page_config(
    page_title="Tender Intelligence",
    page_icon="📊",
    layout="wide"
)

db.init_db()
db.ensure_super_admin()

if "user" not in st.session_state:
    st.session_state.user = None

if "super_admin" not in st.session_state:
    st.session_state.super_admin = None


def logout():
    st.session_state.user = None
    st.session_state.super_admin = None
    st.rerun()


def money(value):
    try:
        return f"R {float(value):,.2f}"
    except Exception:
        return "R 0.00"


if (
    not st.session_state.user
    and not st.session_state.super_admin
):
    st.title("Tender Intelligence")

    st.caption(
        "Find opportunities. Understand requirements. "
        "Know where your business qualifies."
    )

    login_tab, register_tab, admin_tab = st.tabs(
        [
            "Business Login",
            "Register Business",
            "Platform Admin"
        ]
    )

    with login_tab:
        st.subheader("Business Login")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            width="stretch"
        ):
            user = db.authenticate_user(
                email,
                password
            )

            if not user:
                st.error(
                    "Incorrect email or password."
                )

            elif (
                user["organization_status"]
                == "SUSPENDED"
            ):
                st.error(
                    "This business account has been suspended."
                )

            else:
                st.session_state.user = user
                st.rerun()

    with register_tab:
        st.subheader(
            "Register Your Business"
        )

        st.caption(
            "Register once and build your business capability profile."
        )

        with st.form(
            "business_registration"
        ):
            st.markdown(
                "### Business Information"
            )

            business_name = st.text_input(
                "Registered Business Name *"
            )

            registration_number = st.text_input(
                "Company Registration Number"
            )

            business_email = st.text_input(
                "Business Email"
            )

            cellphone = st.text_input(
                "Business Cellphone"
            )

            province = st.selectbox(
                "Primary Province",
                [
                    "Gauteng",
                    "Limpopo",
                    "Mpumalanga",
                    "North West",
                    "Free State",
                    "KwaZulu-Natal",
                    "Eastern Cape",
                    "Western Cape",
                    "Northern Cape",
                    "National"
                ]
            )

            industry = st.text_input(
                "Main Industry / Sector",
                placeholder=(
                    "Construction, Security, ICT, "
                    "Cleaning, Consulting..."
                )
            )

            st.markdown(
                "### Account Administrator"
            )

            full_name = st.text_input(
                "Full Name *"
            )

            user_email = st.text_input(
                "Login Email *"
            )

            password = st.text_input(
                "Create Password *",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm Password *",
                type="password"
            )

            submitted = st.form_submit_button(
                "Create Business Account",
                width="stretch"
            )

        if submitted:
            if not business_name.strip():
                st.error(
                    "Business name is required."
                )

            elif not full_name.strip():
                st.error(
                    "Full name is required."
                )

            elif not user_email.strip():
                st.error(
                    "Login email is required."
                )

            elif len(password) < 8:
                st.error(
                    "Password must be at least 8 characters."
                )

            elif password != confirm_password:
                st.error(
                    "Passwords do not match."
                )

            else:
                success, result = (
                    db.register_business(
                        business_name,
                        registration_number,
                        business_email,
                        cellphone,
                        province,
                        industry,
                        full_name,
                        user_email,
                        password
                    )
                )

                if success:
                    st.success(
                        "Business registered."
                    )

                    st.info(
                        f"Business Number: **{result}**"
                    )

                else:
                    st.error(result)

    with admin_tab:
        st.subheader(
            "Platform Administration"
        )

        st.caption(
            "Platform owner access only."
        )

        admin_email = st.text_input(
            "Administrator Email",
            key="admin_email"
        )

        admin_password = st.text_input(
            "Administrator Password",
            type="password",
            key="admin_password"
        )

        if st.button(
            "Administrator Login",
            width="stretch"
        ):
            admin = (
                db.authenticate_super_admin(
                    admin_email,
                    admin_password
                )
            )

            if admin:
                st.session_state.super_admin = admin
                st.rerun()

            else:
                st.error(
                    "Administrator credentials incorrect."
                )

    st.stop()


if st.session_state.super_admin:
    st.sidebar.title(
        "Tender Intelligence"
    )

    st.sidebar.caption(
        "Platform Control"
    )

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Businesses",
            "Subscriptions",
            "Tender Sources",
            "Tenders",
            "Platform Settings"
        ]
    )

    if st.sidebar.button(
        "Logout",
        width="stretch"
    ):
        logout()

    if menu == "Dashboard":
        st.title(
            "Platform Dashboard"
        )

        metrics = (
            db.platform_metrics()
        )

        c1, c2, c3, c4 = (
            st.columns(4)
        )

        c1.metric(
            "Registered Businesses",
            metrics["organizations"]
        )

        c2.metric(
            "Active Subscribers",
            metrics["active"]
        )

        c3.metric(
            "Trial Accounts",
            metrics["trials"]
        )

        c4.metric(
            "Monthly Revenue",
            money(
                metrics["monthly_revenue"]
            )
        )

        c5, c6, c7 = (
            st.columns(3)
        )

        c5.metric(
            "Suspended",
            metrics["suspended"]
        )

        c6.metric(
            "Tenders Captured",
            metrics["tenders"]
        )

        c7.metric(
            "Tender Matches",
            metrics["matches"]
        )

        st.markdown("---")

        st.subheader(
            "Platform Activity"
        )

        st.info(
            "This will later show registrations, payments, "
            "new tenders and matching activity."
        )

    elif menu == "Businesses":
        st.title(
            "Registered Businesses"
        )

        businesses = (
            db.list_businesses()
        )

        if not businesses:
            st.info(
                "No businesses registered."
            )

        else:
            df = pd.DataFrame(
                businesses
            )

            columns = [
                "business_number",
                "business_name",
                "province",
                "industry",
                "status",
                "plan",
                "subscription_status",
                "monthly_fee"
            ]

            st.dataframe(
                df[columns],
                width="stretch",
                hide_index=True
            )

            st.markdown("---")

            business_map = {
                (
                    f"{b['business_number']} — "
                    f"{b['business_name']}"
                ): b
                for b in businesses
            }

            selected_label = (
                st.selectbox(
                    "Manage Business",
                    list(
                        business_map.keys()
                    )
                )
            )

            selected = (
                business_map[
                    selected_label
                ]
            )

            st.write(
                "**Business:**",
                selected["business_name"]
            )

            st.write(
                "**Registration:**",
                selected["registration_number"]
            )

            st.write(
                "**Province:**",
                selected["province"]
            )

            st.write(
                "**Industry:**",
                selected["industry"]
            )

            statuses = [
                "PENDING",
                "ACTIVE",
                "SUSPENDED"
            ]

            current_status = (
                selected["status"]
                if selected["status"]
                in statuses
                else "PENDING"
            )

            new_status = (
                st.selectbox(
                    "Account Status",
                    statuses,
                    index=statuses.index(
                        current_status
                    )
                )
            )

            if st.button(
                "Update Account Status"
            ):
                db.update_business_status(
                    selected["id"],
                    new_status
                )

                st.success(
                    "Business status updated."
                )

                st.rerun()

    elif menu == "Subscriptions":
        st.title(
            "Subscriptions"
        )

        businesses = (
            db.list_businesses()
        )

        if not businesses:
            st.info(
                "No businesses registered."
            )

        else:
            business_map = {
                (
                    f"{b['business_number']} — "
                    f"{b['business_name']}"
                ): b
                for b in businesses
            }

            selected_label = (
                st.selectbox(
                    "Business",
                    list(
                        business_map.keys()
                    )
                )
            )

            selected = (
                business_map[
                    selected_label
                ]
            )

            plan = st.selectbox(
                "Plan",
                [
                    "STARTER",
                    "PROFESSIONAL",
                    "BUSINESS"
                ]
            )

            monthly_fee = st.number_input(
                "Monthly Fee (R)",
                min_value=0.0,
                step=100.0
            )

            subscription_status = (
                st.selectbox(
                    "Subscription Status",
                    [
                        "TRIAL",
                        "ACTIVE",
                        "PAST_DUE",
                        "CANCELLED"
                    ]
                )
            )

            if st.button(
                "Update Subscription",
                width="stretch"
            ):
                db.update_subscription(
                    selected["id"],
                    plan,
                    monthly_fee,
                    subscription_status
                )

                st.success(
                    "Subscription updated."
                )

                st.rerun()

    elif menu == "Tender Sources":
        st.title(
            "Tender Sources"
        )

        st.info(
            "This is where we will connect automated tender sourcing."
        )

        st.markdown("""
        Planned sources:

        - National Treasury eTender
        - Municipal portals
        - Provincial departments
        - SOEs
        - Universities
        - Public entities
        - Private procurement sources
        """)

    elif menu == "Tenders":
        st.title(
            "Tender Management"
        )

        st.info(
            "Tender ingestion and analysis comes next."
        )

    elif menu == "Platform Settings":
        st.title(
            "Platform Settings"
        )

        st.info(
            "Subscription plans, notifications and matching "
            "settings will be controlled here."
        )

    st.stop()


user = st.session_state.user
org_id = user["org_id"]

st.sidebar.title(
    "Tender Intelligence"
)

st.sidebar.caption(
    f"{user['business_name']}\n"
    f"{user['business_number']}"
)

menu = st.sidebar.radio(
    "Navigation",
    [
        "Opportunity Radar",
        "Tender Finder",
        "Almost Qualified",
        "Company Profile",
        "Compliance",
        "Bid Tracker",
        "Account"
    ]
)

if st.sidebar.button(
    "Logout",
    width="stretch"
):
    logout()


if menu == "Opportunity Radar":
    st.title(
        "Opportunity Radar"
    )

    st.caption(
        "Opportunities matched to your business."
    )

    metrics = (
        db.business_dashboard_metrics(
            org_id
        )
    )

    c1, c2, c3, c4 = (
        st.columns(4)
    )

    c1.metric(
        "Matched Opportunities",
        metrics["total_matches"]
    )

    c2.metric(
        "Strong Matches",
        metrics["strong_matches"]
    )

    c3.metric(
        "Almost Qualified",
        metrics["almost"]
    )

    c4.metric(
        "Not Eligible",
        metrics["not_eligible"]
    )

    st.markdown("---")

    st.subheader(
        "Your Opportunity Feed"
    )

    st.info(
        "Once tender sourcing is connected, matched opportunities "
        "will appear here automatically."
    )

elif menu == "Tender Finder":
    st.title(
        "Tender Finder"
    )

    search = st.text_input(
        "What are you looking for?",
        placeholder=(
            "Security, ICT, construction, consulting..."
        )
    )

    province = st.selectbox(
        "Province",
        [
            "All",
            "Gauteng",
            "Limpopo",
            "Mpumalanga",
            "North West",
            "Free State",
            "KwaZulu-Natal",
            "Eastern Cape",
            "Western Cape",
            "Northern Cape",
            "National"
        ]
    )

    st.info(
        "Live tender search will be connected next."
    )

elif menu == "Almost Qualified":
    st.title(
        "Almost Qualified"
    )

    st.caption(
        "Opportunities your business nearly qualifies for."
    )

    st.info(
        "The system will show exactly which requirements are missing."
    )

elif menu == "Company Profile":
    st.title(
        "Business Capability Profile"
    )

    st.caption(
        "This profile will drive automatic tender matching."
    )

    profile = (
        db.get_company_profile(
            org_id
        )
    )

    with st.form(
        "company_profile"
    ):
        trading_name = (
            st.text_input(
                "Trading Name",
                value=profile.get(
                    "trading_name",
                    ""
                ) or ""
            )
        )

        company_description = (
            st.text_area(
                "Describe Your Business",
                value=profile.get(
                    "company_description",
                    ""
                ) or "",
                height=120
            )
        )

        c1, c2 = (
            st.columns(2)
        )

        with c1:
            bbbee_level = (
                st.text_input(
                    "B-BBEE Level",
                    value=profile.get(
                        "bbbee_level",
                        ""
                    ) or ""
                )
            )

            csd_number = (
                st.text_input(
                    "CSD Number",
                    value=profile.get(
                        "csd_number",
                        ""
                    ) or ""
                )
            )

            cidb_grading = (
                st.text_input(
                    "CIDB Grading",
                    value=profile.get(
                        "cidb_grading",
                        ""
                    ) or ""
                )
            )

            vat_number = (
                st.text_input(
                    "VAT Number",
                    value=profile.get(
                        "vat_number",
                        ""
                    ) or ""
                )
            )

        with c2:
            years_in_business = (
                st.number_input(
                    "Years in Business",
                    min_value=0,
                    value=int(
                        profile.get(
                            "years_in_business"
                        ) or 0
                    )
                )
            )

            employee_count = (
                st.number_input(
                    "Number of Employees",
                    min_value=0,
                    value=int(
                        profile.get(
                            "employee_count"
                        ) or 0
                    )
                )
            )

            turnover_options = [
                "Under R1m",
                "R1m - R5m",
                "R5m - R10m",
                "R10m - R50m",
                "R50m - R100m",
                "Above R100m"
            ]

            existing_turnover = (
                profile.get(
                    "turnover_band"
                )
            )

            turnover_index = (
                turnover_options.index(
                    existing_turnover
                )
                if existing_turnover
                in turnover_options
                else 0
            )

            turnover_band = (
                st.selectbox(
                    "Annual Turnover",
                    turnover_options,
                    index=turnover_index
                )
            )

        provinces = (
            st.text_area(
                "Provinces / Areas Served",
                value=profile.get(
                    "provinces",
                    ""
                ) or ""
            )
        )

        services = (
            st.text_area(
                "Products / Services",
                value=profile.get(
                    "services",
                    ""
                ) or "",
                placeholder=(
                    "List the products and services your company offers."
                )
            )
        )

        certifications = (
            st.text_area(
                "Certifications",
                value=profile.get(
                    "certifications",
                    ""
                ) or ""
            )
        )

        licences = (
            st.text_area(
                "Licences / Registrations",
                value=profile.get(
                    "licences",
                    ""
                ) or ""
            )
        )

        c3, c4 = (
            st.columns(2)
        )

        with c3:
            minimum_contract_value = (
                st.number_input(
                    "Preferred Minimum Tender Value",
                    min_value=0.0,
                    value=float(
                        profile.get(
                            "minimum_contract_value"
                        ) or 0
                    )
                )
            )

        with c4:
            maximum_contract_value = (
                st.number_input(
                    "Maximum Contract Value You Can Handle",
                    min_value=0.0,
                    value=float(
                        profile.get(
                            "maximum_contract_value"
                        ) or 0
                    )
                )
            )

        save = (
            st.form_submit_button(
                "Save Capability Profile",
                width="stretch"
            )
        )

    if save:
        db.save_company_profile(
            org_id,
            trading_name,
            company_description,
            bbbee_level,
            csd_number,
            cidb_grading,
            vat_number,
            years_in_business,
            employee_count,
            turnover_band,
            provinces,
            services,
            certifications,
            licences,
            minimum_contract_value,
            maximum_contract_value
        )

        st.success(
            "Capability profile saved."
        )

elif menu == "Compliance":
    st.title(
        "Compliance Wallet"
    )

    st.info(
        """
        Next we add:

        • CSD  
        • Tax Compliance  
        • B-BBEE  
        • CIDB  
        • COIDA  
        • Insurance  
        • Industry certificates  
        • Expiry-date alerts
        """
    )

elif menu == "Bid Tracker":
    st.title(
        "Bid Tracker"
    )

    st.info(
        "Track opportunities through Preparing → Submitted → "
        "Awarded / Unsuccessful."
    )

elif menu == "Account":
    st.title(
        "Account"
    )

    st.write(
        "**Business:**",
        user["business_name"]
    )

    st.write(
        "**Business Number:**",
        user["business_number"]
    )

    st.write(
        "**User:**",
        user["full_name"]
    )

    st.write(
        "**Role:**",
        user["role"]
    )

    st.write(
        "**Account Status:**",
        user["organization_status"]
    )