import streamlit as st
import whois
import socket
import dns.resolver

# --- Configuration ---
# 1. FIX: Changed 'sidebar' to 'wide' for the layout, as 'sidebar' is not a valid option.
# 2. FIX: Ensured this is the first st. command to prevent StreamlitInvalidPageLayoutError.
st.set_page_config(page_title="Support Tools", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("Support Tools")
tool_selection = st.sidebar.radio(
    "Select Tool:",
    ("Domain Check", "IP Lookup", "DNS Records", "SSL Check (Not implemented here)")
)
st.sidebar.markdown("---")

# --- WHOIS Helper Function ---

def get_whois_data(domain):
    """Fetches WHOIS data for a domain with robust error handling."""
    try:
        # Tries to perform the WHOIS lookup
        w = whois.whois(domain)
        # FIX: The successful result returns True and the data
        return True, w
    except whois.exceptions.FailedParsing as e:
        # FIX: Handles the specific FailedParsing error shown in your screenshot
        st.error(f"WHOIS Parsing Error: Failed to parse WHOIS data for {domain}. The structure might be non-standard.")
        st.exception(e)
        return False, None
    except Exception as e:
        # General WHOIS lookup error
        st.error(f"An unexpected error occurred during WHOIS lookup for {domain}.")
        st.exception(e)
        return False, None

# --- Application Logic Based on Tool Selection ---

if tool_selection == "Domain Check":
    st.header("🌐 Domain Check")
    # FIX: Added .strip() to clean whitespace from input
    domain = st.text_input("Enter Domain Name (e.g., google.com)", value="streamlit.io").strip()

    if domain:
        st.subheader("Domain Registration & WHOIS Information")
        
        # 1. SOA Record Check
        try:
            answers = dns.resolver.resolve(domain, 'SOA')
            st.success("✅ SOA record found")
            for rdata in answers:
                # Displays SOA record data
                st.code(f"{rdata.mname}. {rdata.rname}. {rdata.serial} {rdata.refresh} {rdata.retry} {rdata.expire} {rdata.minimum}")

        except dns.resolver.NoAnswer:
            st.warning("⚠️ No SOA record found.")
        except dns.resolver.NXDOMAIN:
            st.error("❌ Domain does not exist (NXDOMAIN).")
        except Exception as e:
            st.warning(f"Error checking SOA record: {e}")

        st.markdown("---")

        # 2. WHOIS Lookup
        whois_success, whois_data = get_whois_data(domain)

        # FIX: This block uses the return values from the helper function 
        # to ensure correct logic and indentation (line 218 fix).
        if whois_success and whois_data: 
            st.success("WHOIS Data Retrieved Successfully")

            # Display key WHOIS fields cleanly
            data = {
                "Registrar": whois_data.registrar,
                "Creation Date": whois_data.creation_date,
                "Expiration Date": whois_data.expiration_date,
                "Updated Date": whois_data.updated_date,
                "Name Servers": whois_data.name_servers,
                "Status": whois_data.status
            }

            display_data = {k: v for k, v in data.items() if v is not None}
            st.json(display_data)

            with st.expander("View Full WHOIS Record"):
                st.text(whois_data) 

elif tool_selection == "IP Lookup":
    st.header("📍 IP Lookup")
    host = st.text_input("Enter Domain or Hostname (e.g., google.com)", value="www.google.com").strip()

    if host:
        try:
            ip_address = socket.gethostbyname(host)
            st.success(f"IP Address for **{host}** is **{ip_address}**")
        except socket.gaierror:
            st.error(f"Could not resolve the hostname: **{host}**")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

elif tool_selection == "DNS Records":
    st.header("📜 DNS Records")
    domain = st.text_input("Enter Domain Name for DNS Query", value="streamlit.io").strip()
    record_type = st.selectbox("Select Record Type", ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME'])

    if domain:
        st.subheader(f"Querying {record_type} records for {domain}")
        try:
            answers = dns.resolver.resolve(domain, record_type)
            st.success(f"{len(answers)} record(s) found.")
            results = []
            for rdata in answers:
                if record_type == 'MX':
                    results.append(f"Preference: {rdata.preference}, Mail Exchanger: {rdata.exchange}")
                elif record_type == 'TXT':
                    # Handle multi-string TXT records
                    txt_data = b"".join(rdata.strings).decode()
                    results.append(f"TXT Data: {txt_data}")
                else:
                    results.append(str(rdata))

            st.code("\n".join(results))

        except dns.resolver.NoAnswer:
            st.info(f"No {record_type} record found for {domain}.")
        except dns.resolver.NXDOMAIN:
            st.error(f"Domain **{domain}** does not exist.")
        except Exception as e:
            st.error(f"An error occurred during DNS query: {e}")

elif tool_selection == "SSL Check (Not implemented here)":
    st.header("🔒 SSL Check")
    st.info("This section is a placeholder for future SSL/TLS checking functionality.")

# --- Footer/Credits ---
st.sidebar.markdown("---")
st.sidebar.caption("Support Tools Demo")
