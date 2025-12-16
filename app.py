import streamlit as st
import requests
import json
from datetime import datetime
import socket
import ssl

# --- MINIMAL CHANGE 1: Import the whois library and its exceptions ---
import whois
from whois import exceptions
# import subprocess # REMOVED: Replaced with robust python-whois library call

st.set_page_config(
    page_title="Level 1 Tech Support Toolkit",
    page_icon="🔧",
    layout="wide"
)

st.sidebar.title("🔧 Support Tools")
tool = st.sidebar.radio(
    "Select Tool:",
    ["Domain Check", "My IP", "IP Lookup", "DNS Records", "SSL Check"]
)

st.title("Level 1 Tech Support Toolkit")
st.markdown("Essential diagnostic tools for first-line support")

if tool == "Domain Check":
    st.header("🌐 Comprehensive Domain Status Check")
    st.markdown("Check domain registration, DNS configuration, and nameserver status")
    
    domain = st.text_input("Enter domain:", placeholder="example.com")
    if st.button("Check Domain Status"):
        if domain:
            domain = domain.strip().lower()
            
            with st.spinner("Performing comprehensive domain check..."):
                # Initialize status tracking
                issues = []
                warnings = []
                success_checks = []
                
                # 1. DNS Resolution Check
                st.subheader("🔍 DNS Resolution Status")
                try:
                    response = requests.get(f"https://dns.google/resolve?name={domain}&type=A", timeout=5)
                    data = response.json()
                    
                    if data.get('Status') == 0 and data.get('Answer'):
                        st.success(f"✅ Domain {domain} is resolving")
                        success_checks.append("DNS resolution working")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**A Records (IPv4):**")
                            for record in data['Answer']:
                                st.code(record['data'])
                        
                        # Check for IPv6
                        try:
                            ipv6_response = requests.get(f"https://dns.google/resolve?name={domain}&type=AAAA", timeout=5)
                            ipv6_data = ipv6_response.json()
                            if ipv6_data.get('Answer'):
                                with col2:
                                    st.write("**AAAA Records (IPv6):**")
                                    for record in ipv6_data['Answer'][:3]:
                                        st.code(record['data'])
                        except:
                            pass
                            
                    elif data.get('Status') == 3:
                        st.error("❌ Domain name does not exist (NXDOMAIN)")
                        issues.append("Domain not registered or expired")
                    else:
                        st.error("❌ Domain not resolving")
                        issues.append("DNS resolution failed")
                        
                except Exception as e:
                    st.error(f"❌ DNS check failed: {str(e)}")
                    issues.append(f"DNS error: {str(e)}")
                
                # 2. Nameserver Check
                st.subheader("🖥️ Nameserver Configuration")
                try:
                    ns_response = requests.get(f"https://dns.google/resolve?name={domain}&type=NS", timeout=5)
                    ns_data = ns_response.json()
                    
                    if ns_data.get('Answer'):
                        nameservers = [record['data'].rstrip('.') for record in ns_data['Answer']]
                        
                        if len(nameservers) >= 2:
                            st.success(f"✅ Found {len(nameservers)} nameservers (redundancy good)")
                            success_checks.append("Multiple nameservers configured")
                        elif len(nameservers) == 1:
                            st.warning("⚠️ Only 1 nameserver found (should have at least 2 for redundancy)")
                            warnings.append("Insufficient nameserver redundancy")
                        
                        for ns in nameservers:
                            st.code(ns)
                            
                    else:
                        st.error("❌ No authoritative nameservers found")
                        issues.append("No nameservers configured - domain may be on hold or suspended")
                        st.warning("""
                        **Common causes:**
                        - Domain recently registered but nameservers not set
                        - Domain suspended for verification (.co.za domains)
                        - Domain on registrar hold
                        - Expired domain in grace period
                        """)
                        
                except Exception as e:
                    st.error(f"❌ Nameserver check failed: {str(e)}")
                    issues.append("Could not retrieve nameserver information")
                
                # 3. SOA Record Check (shows domain authority and refresh info)
                st.subheader("📋 SOA (Start of Authority) Record")
                try:
                    soa_response = requests.get(f"https://dns.google/resolve?name={domain}&type=SOA", timeout=5)
                    soa_data = soa_response.json()
                    
                    if soa_data.get('Answer'):
                        soa_record = soa_data['Answer'][0]['data']
                        st.success("✅ SOA record found")
                        st.code(soa_record)
                        success_checks.append("SOA record configured")
                    else:
                        st.warning("⚠️ No SOA record found")
                        warnings.append("Missing SOA record")
                        
                except Exception as e:
                    st.warning(f"⚠️ Could not check SOA: {str(e)}")
                
                # --- MINIMAL CHANGE 2: Simplified and fixed WHOIS block using python-whois ---
                st.subheader("📝 Domain Registration & WHOIS Information")
                
                whois_data = None
                whois_success = False
                whois_error_message = None

                try:
                    # FIX: Use the dedicated whois library call
                    whois_data = whois.whois(domain)
                    whois_success = True
                    
                except exceptions.FailedParsing as e:
                    # FIX: Handles the specific FailedParsing error reported previously
                    whois_error_message = "WHOIS Parsing Error: The WHOIS server returned data in an unexpected format."
                    st.error(f"❌ WHOIS check failed: {whois_error_message}")
                    st.caption("See Raw WHOIS Output below for details.")
                    
                except exceptions.WhoisCommandFailed as e:
                    whois_error_message = "WHOIS Command Failed: Unable to connect to the WHOIS server."
                    st.error(f"❌ WHOIS check failed: {whois_error_message}")

                except Exception as e:
                    whois_error_message = f"WHOIS Lookup Error: {type(e).__name__}"
                    st.error(f"❌ WHOIS check failed: {whois_error_message}")

                # --- Display the WHOIS data if successful ---
                if whois_success and whois_data and whois_data.domain_name:
                    st.success("✅ WHOIS information retrieved")
                    success_checks.append("WHOIS lookup successful")

                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Domain:** {domain}")
                        
                        registrar = whois_data.registrar
                        if registrar:
                            st.write(f"**Registrar:** {registrar}")

                        status_list = whois_data.status
                        if status_list:
                            st.write("**Domain Status:**")
                            # Ensure status_list is a list, as it can be a string
                            if not isinstance(status_list, list):
                                status_list = [status_list] if status_list else []
                                
                            for status in status_list[:5]:
                                status_lower = str(status).lower()
                                if any(x in status_lower for x in ['ok', 'active', 'registered']):
                                    st.success(f"✅ {status.split()[0]}")
                                elif any(x in status_lower for x in ['hold', 'lock', 'suspended', 'pending delete']):
                                    st.error(f"❌ {status.split()[0]}")
                                    issues.append(f"Domain status: {status.split()[0]}")
                                elif any(x in status_lower for x in ['pending', 'verification', 'grace', 'expired']):
                                    st.warning(f"⚠️ {status.split()[0]}")
                                    if 'expired' in status_lower:
                                        issues.append(f"Domain is expired")
                                    else:
                                        warnings.append(f"Domain status: {status.split()[0]}")
                                else:
                                    st.info(f"ℹ️ {status.split()[0]}")
                        
                        registrant = whois_data.registrant
                        if registrant and 'redacted' not in str(registrant).lower():
                            st.write(f"**Registrant:** {registrant}")

                    with col2:
                        created_date = whois_data.creation_date
                        expires_date = whois_data.expiration_date
                        updated_date = whois_data.updated_date
                        
                        if created_date:
                            st.write(f"**Created:** {str(created_date).split()[0]}")
                        
                        if updated_date:
                            st.write(f"**Updated:** {str(updated_date).split()[0]}")
                        
                        if expires_date:
                            st.write(f"**Expires:** {str(expires_date).split()[0]}")
                            # Expiration check
                            try:
                                # Ensure we are checking against a single datetime object
                                if isinstance(expires_date, list):
                                    expiry = expires_date[0]
                                else:
                                    expiry = expires_date
                                    
                                if expiry:
                                    days_left = (expiry - datetime.now().replace(microsecond=0)).days
                                    
                                    if days_left < 0:
                                        st.error(f"❌ EXPIRED {abs(days_left)} days ago!")
                                        issues.append(f"Domain expired {abs(days_left)} days ago")
                                    elif days_left < 30:
                                        st.error(f"⚠️ {days_left} days - URGENT!")
                                        issues.append(f"Expires in {days_left} days")
                                    elif days_left < 90:
                                        st.warning(f"⚠️ {days_left} days")
                                        warnings.append(f"Expires in {days_left} days")
                                    else:
                                        st.success(f"✅ {days_left} days")
                            except:
                                pass # ignore datetime calculation errors
                    
                    nameservers = whois_data.name_servers
                    if nameservers:
                        st.write("**WHOIS Nameservers:**")
                        for ns in nameservers[:3]:
                            st.caption(f"• {str(ns).lower().rstrip('.')}")
                    
                    with st.expander("📄 View Full Raw WHOIS Record"):
                        st.json(whois_data) # Use JSON for structured output

                # Display the API fallback/manual lookup instructions if the library failed
                else:
                    st.warning("⚠️ Could not retrieve WHOIS information via automated library.")
                    if whois_error_message:
                        st.caption(f"Reason: {whois_error_message}")

                    st.info(f"""
                    **Try manual lookup at:**
                    - [ICANN Lookup](https://lookup.icann.org/en/lookup?name={domain})
                    - [Who.is](https://who.is/whois/{domain})
                    """)
                    warnings.append("WHOIS data unavailable via automated tools")

                # 5. Summary Report
                st.divider()
                st.subheader("📊 Domain Health Summary")
                
                if not issues and not warnings:
                    st.success("🎉 **Domain is healthy!** All checks passed.")
                    st.balloons()
                else:
                    if issues:
                        with st.expander("❌ Critical Issues", expanded=True):
                            for issue in issues:
                                st.error(f"• {issue}")
                    
                    if warnings:
                        with st.expander("⚠️ Warnings", expanded=True):
                            for warning in warnings:
                                st.warning(f"• {warning}")
                    
                    if success_checks:
                        with st.expander("✅ Passed Checks"):
                            for check in success_checks:
                                st.success(f"• {check}")
                
                # Troubleshooting tips
                if issues or warnings:
                    with st.expander("💡 Troubleshooting Tips"):
                        st.markdown("""
                        **Common Issues & Solutions:**
                        
                        **No Nameservers / Domain on Hold:**
                        - For .co.za domains: Complete COZA verification process with your registrar.
                        - Check if domain has expired and is in the redemption or grace period.
                        - Ensure nameservers are set correctly at your registrar.

                        **WHOIS Parsing Error:**
                        - The WHOIS response format may be non-standard for this specific TLD (especially ccTLDs).
                        - Use the manual lookup links provided above.
                        """)
# --- Remaining Tool sections (My IP, IP Lookup, DNS Records, SSL Check) go here ---

if tool == "My IP":
    st.header("📍 My Public IP Address")
    # ... (Your existing code for My IP)
    
if tool == "IP Lookup":
    st.header("🔍 IP Geolocation Lookup")
    # ... (Your existing code for IP Lookup)

if tool == "DNS Records":
    st.header("📜 DNS Record Lookup")
    # ... (Your existing code for DNS Records)

if tool == "SSL Check":
    st.header("🔒 SSL Certificate Check")
    # ... (Your existing code for SSL Check)
