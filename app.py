import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(
    page_title="Level 1 Tech Support Toolkit",
    page_icon="🔧",
    layout="wide"
)

st.sidebar.title("🔧 Support Tools")
tool = st.sidebar.radio(
    "Select Tool:",
    ["Domain Check", "My IP", "DNS Records", "SSL Check"]
)

st.title("Level 1 Tech Support Toolkit")
st.markdown("Essential diagnostic tools for first-line support")

if tool == "Domain Check":
    st.header("🌐 Domain Status Check")
    domain = st.text_input("Enter domain:", placeholder="example.com")
    if st.button("Check Domain"):
        if domain:
            with st.spinner("Checking..."):
                try:
                    response = requests.get(f"https://dns.google/resolve?name={domain}&type=A")
                    data = response.json()
                    if data.get('Status') == 0:
                        st.success(f"✅ Domain {domain} is active and resolving")
                        if data.get('Answer'):
                            st.subheader("IP Addresses:")
                            for record in data['Answer']:
                                st.code(record['data'])
                    else:
                        st.error("❌ Domain not found or not resolving")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

elif tool == "My IP":
    st.header("📍 Network IP Lookup")
    if st.button("Get My IP"):
        with st.spinner("Fetching..."):
            try:
                ip = requests.get("https://api.ipify.org?format=json").json()['ip']
                geo_data = requests.get(f"https://ipapi.co/{ip}/json/").json()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("IP Address", ip)
                    st.metric("City", geo_data.get('city', 'N/A'))
                with col2:
                    st.metric("Country", geo_data.get('country_name', 'N/A'))
                    st.metric("ISP", geo_data.get('org', 'N/A'))
            except Exception as e:
                st.error(f"Error: {str(e)}")

elif tool == "DNS Records":
    st.header("🗂️ DNS Record Retrieval")
    domain = st.text_input("Enter domain:", placeholder="example.com")
    if st.button("Lookup DNS"):
        if domain:
            with st.spinner("Fetching records..."):
                record_types = ['A', 'MX', 'TXT', 'NS', 'CNAME']
                results = {}
                for record_type in record_types:
                    try:
                        response = requests.get(
                            f"https://dns.google/resolve?name={domain}&type={record_type}"
                        )
                        data = response.json()
                        if data.get('Answer'):
                            results[record_type] = [r['data'] for r in data['Answer']]
                    except:
                        continue
                if results:
                    for record_type, records in results.items():
                        st.subheader(f"{record_type} Records")
                        for record in records:
                            st.code(record)
                else:
                    st.warning("No records found")

elif tool == "SSL Check":
    st.header("🔒 SSL Certificate Check")
    domain = st.text_input("Enter domain (without https://):", placeholder="example.com")
    if st.button("Check SSL"):
        if domain:
            # Remove any protocol prefix if user included it
            domain = domain.replace('https://', '').replace('http://', '').split('/')[0]
            
            with st.spinner("Checking SSL certificate..."):
                try:
                    # Using SSL Labs API (free, no auth required)
                    api_url = f"https://api.ssllabs.com/api/v3/analyze?host={domain}&publish=off&all=done"
                    
                    # Start the scan
                    response = requests.get(api_url)
                    data = response.json()
                    
                    if data.get('status') == 'READY':
                        st.success(f"✅ SSL Certificate found for {domain}")
                        
                        # Display certificate info
                        if data.get('endpoints'):
                            for endpoint in data['endpoints']:
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Grade", endpoint.get('grade', 'N/A'))
                                    st.metric("IP Address", endpoint.get('ipAddress', 'N/A'))
                                with col2:
                                    st.metric("Status", endpoint.get('statusMessage', 'N/A'))
                                    
                        st.info("💡 For detailed SSL analysis, visit: https://www.ssllabs.com/ssltest/")
                    else:
                        # Alternative: Use a simpler SSL checker
                        st.info("⏳ Starting SSL scan... This may take a moment.")
                        st.markdown(f"""
                        **Quick SSL Check Options:**
                        - [SSL Labs Test](https://www.ssllabs.com/ssltest/analyze.html?d={domain})
                        - [SSL Checker](https://www.sslshopper.com/ssl-checker.html#{domain})
                        
                        **What to verify:**
                        - ✓ Certificate is valid and not expired
                        - ✓ Certificate matches the domain
                        - ✓ Certificate chain is complete
                        - ✓ No security warnings
                        """)
                        
                except Exception as e:
                    st.warning("SSL Labs API may be busy. Here are alternative options:")
                    st.markdown(f"""
                    **Check SSL Certificate at:**
                    - [SSL Labs](https://www.ssllabs.com/ssltest/analyze.html?d={domain})
                    - [SSL Checker](https://www.sslshopper.com/ssl-checker.html#{domain})
                    - [DigiCert SSL Tool](https://www.digicert.com/help/)
                    
                    **Common SSL Issues:**
                    - 🔴 Expired certificate
                    - 🔴 Certificate name mismatch
                    - 🔴 Untrusted certificate authority
                    - 🔴 Incomplete certificate chain
                    """)
        else:
            st.warning("Please enter a domain name")