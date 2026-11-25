import streamlit as st
import pandas as pd
from api import api_request, APIError, login_user, register_student

st.set_page_config(page_title="College Library Management System", page_icon="📚", layout="wide")
st.title("📚 College Library Management System")
st.caption("Book catalogue, member services and borrowing management")

if "token" not in st.session_state: st.session_state.token = None
if "user" not in st.session_state: st.session_state.user = None

def call(method, path, data=None, params=None, auth=True):
    return api_request(method, path, token=st.session_state.token if auth else None, data=data, params=params)

def show_error(err): st.error(str(err))

with st.sidebar:
    st.subheader("Account")
    if st.session_state.token:
        st.success(f"Signed in: {st.session_state.user.get('email','User')}")
        st.caption(f"Role: {st.session_state.user.get('role','unknown')}")
        if st.button("Sign out", use_container_width=True):
            st.session_state.token = None; st.session_state.user = None; st.rerun()
    else:
        mode = st.radio("Choose", ["Login", "Student registration"])
        with st.form("account_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            member_id = st.number_input("Library Member ID", min_value=1, step=1) if mode == "Student registration" else None
            submitted = st.form_submit_button("Continue", use_container_width=True)
        if submitted:
            try:
                if mode == "Login":
                    result = login_user(email.strip(), password)
                    st.session_state.token = result["access_token"]
                    st.session_state.user = call("GET", "/auth/me")
                else:
                    register_student(email.strip(), password, int(member_id))
                    st.success("Registration complete. Please log in.")
                st.rerun()
            except APIError as e: show_error(e)

st.markdown("---")
tabs = st.tabs(["Overview", "Books", "Members", "Borrowings", "Administration"])

with tabs[0]:
    st.subheader("Library overview")
    try:
        stats = call("GET", "/dashboard", auth=False)
        cols = st.columns(4)
        for col, (label, key) in zip(cols, [("Total copies", "total_books"),("Members", "total_members"),("Active borrowings", "active_borrowings"),("Available copies", "available_books")]):
            col.metric(label, stats.get(key, 0))
    except APIError as e: show_error(e)
    st.info("Sign in to access member-specific services and staff operations.")

with tabs[1]:
    st.subheader("Book catalogue")
    search = st.text_input("Search by title", key="book_search")
    try:
        books = call("GET", "/books/search", params={"title": search}, auth=False) if search else call("GET", "/books/", auth=False)
        if books: st.dataframe(pd.DataFrame(books), use_container_width=True, hide_index=True)
        else: st.info("No books found.")
    except APIError as e: show_error(e)
    if st.session_state.token and st.session_state.user.get("role") in ["admin", "librarian"]:
        with st.expander("Add a book"):
            with st.form("add_book"):
                title=st.text_input("Title"); author=st.text_input("Author"); category=st.text_input("Category"); copies=st.number_input("Total copies", min_value=1, step=1)
                if st.form_submit_button("Add book"):
                    try: call("POST", "/books/", {"title":title,"author":author,"category":category,"total_copies":int(copies)}); st.success("Book added."); st.rerun()
                    except APIError as e: show_error(e)

with tabs[2]:
    st.subheader("Members")
    if not st.session_state.token: st.warning("Please log in as a librarian or admin.")
    elif st.session_state.user.get("role") not in ["admin", "librarian"]: st.warning("This section is for library staff.")
    else:
        try:
            members=call("GET", "/members/")
            if members: st.dataframe(pd.DataFrame(members), use_container_width=True, hide_index=True)
            else: st.info("No members registered yet.")
        except APIError as e: show_error(e)
        with st.expander("Register a member"):
            with st.form("new_member"):
                name=st.text_input("Member name"); mem_email=st.text_input("Member email"); phone=st.text_input("Phone")
                if st.form_submit_button("Register member"):
                    try: call("POST", "/members/", {"name":name,"email":mem_email,"phone":phone or None}); st.success("Member registered."); st.rerun()
                    except APIError as e: show_error(e)

with tabs[3]:
    st.subheader("Borrowing records")
    if not st.session_state.token: st.warning("Please log in to view borrowing records.")
    else:
        try:
            records=call("GET", "/borrowings/")
            if records: st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
            else: st.info("No borrowing records found.")
        except APIError as e: show_error(e)
        if st.session_state.user.get("role") == "student":
            with st.form("borrow_book"):
                book_id=st.number_input("Book ID to borrow", min_value=1, step=1)
                if st.form_submit_button("Borrow book"):
                    try: call("POST", "/borrowings/borrow", {"book_id":int(book_id)}); st.success("Borrow request completed."); st.rerun()
                    except APIError as e: show_error(e)
        elif st.session_state.user.get("role") in ["admin", "librarian"]:
            with st.form("return_book"):
                record_id=st.number_input("Borrowing record ID to return", min_value=1, step=1)
                if st.form_submit_button("Process return"):
                    try: call("PUT", f"/borrowings/{int(record_id)}/return"); st.success("Book return processed."); st.rerun()
                    except APIError as e: show_error(e)

with tabs[4]:
    st.subheader("Staff administration")
    if not st.session_state.token or st.session_state.user.get("role") != "admin":
        st.info("Sign in with an administrator account to create librarian accounts.")
    else:
        with st.form("create_staff"):
            staff_email=st.text_input("Staff email"); staff_password=st.text_input("Temporary password (8–72 characters)", type="password"); staff_role=st.selectbox("Role", ["librarian", "admin"])
            if st.form_submit_button("Create staff account"):
                try: call("POST", "/auth/admin/create-user", {"email":staff_email,"password":staff_password,"role":staff_role}); st.success("Staff account created.")
                except APIError as e: show_error(e)
