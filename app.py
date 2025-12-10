import streamlit as st
import requests
import json
from datetime import datetime
import socket
import ssl

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
    
    # Use HTML/JavaScript to fetch IP client-side
    import streamlit.components.v1 as components
    
    # JavaScript to fetch user's actual IP and geolocation
    html_code = """
    <script>
    async function getUserIP() {
        try {
            // Fetch IP from client side
            const ipResponse = await fetch('https://api.ipify.org?format=json');
            const ipData = await ipResponse.json();
            const userIP = ipData.ip;
            
            // Fetch geolocation data
            const geoResponse = await fetch(`https://ipapi.co/${userIP}/json/`);
            let geoData = await geoResponse.json();
            
            // If ipapi.co fails, try fallback
            if (!geoData.city) {
                const fallbackResponse = await fetch(`http://ip-api.com/json/${userIP}`);
                const fallbackData = await fallbackResponse.json();
                geoData = {
                    ip: userIP,
                    city: fallbackData.city,
                    region: fallbackData.regionName,
                    country_name: fallbackData.country,
                    postal: fallbackData.zip,
                    latitude: fallbackData.lat,
                    longitude: fallbackData.lon,
                    org: fallbackData.isp,
                    timezone: fallbackData.timezone
                };
            }
            
            // Send data back to Streamlit
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: geoData
            }, '*');
            
        } catch (error) {
            window.parent.postMessage({
                type: 'streamlit:setComponentValue',
                value: {error: error.message}
            }, '*');
        }
    }
    
    getUserIP();
    </script>
    <div style="padding: 20px; text-align: center;">
        <p>🔍 Detecting your network information...</p>
    </div>
    """
    
    # Render the component and get data
    geo_data = components.html(html_code, height=100)
    
    # Display data once received
    if geo_data and isinstance(geo_data, dict):
        if geo_data.get('error'):
            st.error(f"❌ Error: {geo_data['error']}")
        elif geo_data.get('ip'):
            ip = geo_data.get('ip', 'N/A')
            
            st.success("✅ Network information retrieved successfully")
            
            # Display in organized columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🌐 Public IP", ip)
                st.metric("🏙️ City", geo_data.get('city', 'N/A'))
                st.metric("📮 Postal Code", geo_data.get('postal', 'N/A'))
            
            with col2:
                st.metric("🗺️ Region", geo_data.get('region', 'N/A'))
                st.metric("🌍 Country", geo_data.get('country_name', 'N/A'))
                st.metric("🕐 Timezone", geo_data.get('timezone', 'N/A'))
            
            with col3:
                st.metric("📡 ISP/Provider", geo_data.get('org', 'N/A'))
                if geo_data.get('latitude') and geo_data.get('longitude'):
                    st.metric("📍 Coordinates", f"{geo_data['latitude']:.4f}, {geo_data['longitude']:.4f}")
            
            # Additional details
            with st.expander("🔍 View Additional Details"):
                st.json(geo_data)
        else:
            st.info("🔄 Loading your network information...")
    else:
        st.info("🔄 Loading your network information...")
    
    if st.button("🔄 Refresh Information"):
        st.rerun()

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
    if st.button("Check SSL Certificate"):
        if domain:
            # Clean the domain
            domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0].strip()
            
            with st.spinner(f"Analyzing SSL certificate for {domain}..."):
                try:
                    # Method 1: Try to get certificate directly via Python SSL
                    context = ssl.create_default_context()
                    with socket.create_connection((domain, 443), timeout=10) as sock:
                        with context.wrap_socket(sock, server_hostname=domain) as secure_sock:
                            cert = secure_sock.getpeercert()
                            
                            st.success(f"✅ SSL Certificate found and valid for {domain}")
                            
                            # Parse certificate data
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("📋 Certificate Details")
                                
                                # Subject (who the cert is issued to)
                                subject = dict(x[0] for x in cert['subject'])
                                st.write("**Issued To:**", subject.get('commonName', 'N/A'))
                                
                                # Issuer (who issued the cert)
                                issuer = dict(x[0] for x in cert['issuer'])
                                st.write("**Issued By:**", issuer.get('commonName', 'N/A'))
                                st.write("**Organization:**", issuer.get('organizationName', 'N/A'))
                                
                            with col2:
                                st.subheader("📅 Validity Period")
                                
                                # Dates
                                not_before = cert.get('notBefore')
                                not_after = cert.get('notAfter')
                                
                                st.write("**Valid From:**", not_before)
                                st.write("**Valid Until:**", not_after)
                                
                                # Calculate days remaining
                                if not_after:
                                    try:
                                        expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                                        days_remaining = (expiry_date - datetime.now()).days
                                        
                                        if days_remaining > 30:
                                            st.success(f"✅ **{days_remaining} days** remaining")
                                        elif days_remaining > 0:
                                            st.warning(f"⚠️ **{days_remaining} days** remaining - Renew soon!")
                                        else:
                                            st.error(f"❌ Certificate expired {abs(days_remaining)} days ago")
                                    except:
                                        pass
                            
                            # Subject Alternative Names (SANs)
                            if 'subjectAltName' in cert:
                                st.subheader("🌐 Subject Alternative Names")
                                sans = [san[1] for san in cert['subjectAltName']]
                                for san in sans[:10]:  # Show first 10
                                    st.code(san)
                                if len(sans) > 10:
                                    st.info(f"...and {len(sans) - 10} more domains")
                            
                            # Certificate details in expander
                            with st.expander("🔍 View Full Certificate Details"):
                                st.json(cert)
                                
                except socket.gaierror:
                    st.error(f"❌ Could not resolve domain: {domain}")
                    st.info("💡 Make sure the domain name is correct and accessible")
                    
                except socket.timeout:
                    st.error(f"⏱️ Connection timeout for {domain}")
                    st.info("💡 The server might be slow or blocking connections")
                    
                except ssl.SSLError as ssl_err:
                    st.error(f"❌ SSL Error: {str(ssl_err)}")
                    st.warning("""
                    **Common SSL Issues:**
                    - Certificate has expired
                    - Certificate is self-signed
                    - Certificate name doesn't match domain
                    - Incomplete certificate chain
                    """)
                    
                except Exception as e:
                    st.error(f"❌ Error checking SSL: {str(e)}")
                    st.info(f"💡 Try checking manually at: https://www.ssllabs.com/ssltest/analyze.html?d={domain}")
        else:
            st.warning("⚠️ Please enter a domain name")
