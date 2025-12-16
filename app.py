import streamlit as st
import requests
import json
from datetime import datetime
import socket
import ssl
import whois  # <-- Dedicated WHOIS library

# You MUST run 'pip install python-whois' in your environment

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
                
                # 1. DNS Resolution Check (UNCHANGED)
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
                
                # 2. Nameserver Check (UNCHANGED)
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
                
                # 3. SOA Record Check (UNCHANGED)
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
                
                # 4. WHOIS/Registration Status Check (REVISED SECTION FOR ATTRIBUTE SAFETY)
                st.subheader("📝 Domain Registration & WHOIS Information")
                
                whois_data = {}
                whois_success = False
                whois_raw = None
                tld = domain.split('.')[-1].lower()
                
                # Method 1: Use python-whois library (BEST for gTLDs and ccTLDs)
                try:
                    # Use the library to get the domain object
                    domain_info = whois.query(domain, timeout=15)
                    
                    if domain_info:
                        whois_success = True
                        
                        # Populate a standard dictionary from the whois object - DEFENSIVE ACCESS
                        # Using getattr() ensures that if an attribute is missing (e.g., 'registrar'), 
                        # it defaults cleanly to None or [] instead of crashing.
                        whois_data = {
                            'domain': getattr(domain_info, 'domain_name', domain).rstrip('.').lower(),
                            'registrar': getattr(domain_info, 'registrar', None),
                            'created': getattr(domain_info, 'creation_date', None),
                            'expires': getattr(domain_info, 'expiration_date', None),
                            'updated': getattr(domain_info, 'last_updated', None),
                            
                            # Ensure nameservers is a list of strings
                            'nameservers': [ns.rstrip('.').lower() for ns in getattr(domain_info, 'name_servers', [])] if getattr(domain_info, 'name_servers', []) else [],
                            
                            'status': getattr(domain_info, 'statuses', []),
                            'raw_text': getattr(domain_info, 'text', 'N/A')
                        }
                        
                        whois_raw = whois_data['raw_text']
                        
                        # Registrant Info (often redacted now, but try)
                        reg_name = getattr(domain_info, 'registrant_name', None)
                        reg_org = getattr(domain_info, 'registrant_organization', None)
                        
                        if reg_name and 'redacted' not in str(reg_name).lower():
                            whois_data['registrant'] = reg_name
                        elif reg_org and 'redacted' not in str(reg_org).lower():
                            whois_data['registrant'] = reg_org
                        
                except whois.exceptions.FailedParsing as e:
                    # Occurs when whois server is reached but output format is unexpected
                    st.warning(f"⚠️ WHOIS parsing failed for {tld} (Raw data returned): {str(e)}")
                    # Attempt to capture raw data if possible
                    whois_raw = str(e)
                    whois_data = {}
                    
                except Exception as whois_error:
                    # Catches the generic AttributeError, Timeout, ConnectionError, etc.
                    st.warning(f"⚠️ WHOIS library failed (moving to APIs): {type(whois_error).__name__}: {str(whois_error)}")
                    pass
                
                # Method 2: Try APIs if library failed (starts here)
                if not whois_success:
                    whois_apis = [
                        {
                            'name': 'RDAP',
                            'url': f"https://rdap.org/domain/{domain}",
                            'test': lambda r: r.status_code == 200 and r.json().get('ldhName'),
                            'parser': lambda r: r.json()
                        },
                        {
                            'name': 'IP2WHOIS',
                            'url': f"https://api.ip2whois.com/v2?key=free&domain={domain}",
                            'test': lambda r: r.json().get('domain') is not None and r.json().get('status') != 'EXPIRED',
                            'parser': lambda r: r.json()
                        }
                    ]
                    
                    for api in whois_apis:
                        try:
                            whois_response = requests.get(api['url'], timeout=10)
                            if whois_response.status_code == 200 and api['test'](whois_response):
                                # Overwrite whois_data with API result if successful
                                whois_data = api['parser'](whois_response)
                                if whois_data and (whois_data.get('domain') or whois_data.get('ldhName')):
                                    whois_success = True
                                    break
                        except Exception as api_error:
                            continue

                # --- Display WHOIS Results ---
                if whois_success and whois_data:
                    st.success("✅ WHOIS information retrieved")
                    
                    col1, col2 = st.columns(2)
                    
                    # Date extraction helper function
                    def extract_date(data, keys):
                        for key in keys:
                            date_str = data.get(key)
                            if date_str:
                                # Handles ISO 8601 (from API) and various WHOIS formats
                                try:
                                    if 'T' in str(date_str):
                                        return str(date_str).split('T')[0]
                                    # Fallback for simpler formats
                                    return str(date_str).split(' ')[0]
                                except:
                                    return str(date_str)
                        return None
                        
                    # 1. Dates from RDAP events array (API only)
                    created_date = None
                    expires_date = None
                    updated_date = None
                    
                    if whois_data.get('events'): # RDAP/API format
                        for event in whois_data['events']:
                            action = event.get('eventAction', '').lower()
                            date = event.get('eventDate')
                            if action == 'registration' and not created_date: created_date = date
                            elif action == 'expiration' and not expires_date: expires_date = date
                            elif action in ['last changed', 'last update'] and not updated_date: updated_date = date

                    # 2. Dates from direct fields (WHOIS object or API fallback)
                    if not created_date: created_date = extract_date(whois_data, ['created', 'creation_date', 'create_date', 'createdDate', 'creationDate'])
                    if not expires_date: expires_date = extract_date(whois_data, ['expires', 'expiration_date', 'expiry_date', 'expiresDate', 'expirationDate', 'registry_expiry_date'])
                    if not updated_date: updated_date = extract_date(whois_data, ['updated', 'updated_date', 'update_date', 'updatedDate', 'last_updated'])

                    # Data cleaning and display on the left column
                    with col1:
                        # Domain name
                        domain_name = (whois_data.get('domain') or whois_data.get('domainName') or whois_data.get('ldhName') or domain)
                        st.write(f"**Domain:** {domain_name}")
                        
                        # Registrar
                        registrar = (whois_data.get('registrar') or whois_data.get('registrarName') or whois_data.get('sponsoring_registrar'))
                        if registrar and registrar != 'N/A':
                            st.write(f"**Registrar:** {registrar}")
                        
                        # Registrant
                        registrant = whois_data.get('registrant')
                        if registrant and isinstance(registrant, str) and 'redacted' not in registrant.lower():
                            st.write(f"**Registrant:** {registrant}")

                        # Status
                        status_list = whois_data.get('status', [])
                        if not isinstance(status_list, list): status_list = [status_list] if status_list else []
                        
                        if status_list:
                            st.write("**Domain Status:**")
                            for status_text in status_list[:5]:
                                if isinstance(status_text, dict):
                                    status_text = status_text.get('status', 'Unknown Status')
                                else:
                                    status_text = str(status_text).split()[0]
                                
                                status_lower = status_text.lower()
                                if any(x in status_lower for x in ['ok', 'active', 'registered', 'auto-renew']):
                                    st.success(f"✅ {status_text}")
                                    if "Domain status: Active/OK" not in success_checks: success_checks.append("Domain status: Active/OK")
                                elif any(x in status_lower for x in ['hold', 'lock', 'frozen', 'suspended', 'pending delete']):
                                    st.error(f"❌ {status_text}")
                                    issues.append(f"Domain issue: {status_text}")
                                elif any(x in status_lower for x in ['pending', 'verification', 'grace']):
                                    st.warning(f"⚠️ {status_text}")
                                    warnings.append(f"Domain status: {status_text}")
                                elif 'expired' in status_lower:
                                    st.error(f"❌ {status_text}")
                                    issues.append(f"Domain expired")
                                else:
                                    st.info(f"ℹ️ {status_text}")

                    # Date and Nameserver display on the right column
                    with col2:
                        if created_date: st.write(f"**Created:** {created_date}")
                        if updated_date: st.write(f"**Updated:** {updated_date}")
                        
                        if expires_date:
                            st.write(f"**Expires:** {expires_date}")
                            try:
                                expiry = datetime.strptime(str(expires_date).split('T')[0], '%Y-%m-%d')
                                days_left = (expiry - datetime.now()).days
                                
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
                                pass
                                
                        # Nameservers - handle mixed WHOIS object/RDAP format
                        nameservers = whois_data.get('nameservers')
                        if not nameservers and isinstance(whois_data.get('nameservers'), list): # Handle RDAP nameserver list
                            nameservers = []
                            for ns in whois_data.get('nameservers', []):
                                if isinstance(ns, dict):
                                    nameservers.append(ns.get('ldhName') or ns.get('unicodeName'))
                                elif isinstance(ns, str):
                                    nameservers.append(ns)
                                    
                        if nameservers:
                            st.write("**WHOIS Nameservers:**")
                            for ns in nameservers[:3]:
                                ns_clean = str(ns).lower().rstrip('.')
                                st.caption(f"• {ns_clean}")
                    
                    with st.expander("📄 View Technical/Raw Data"):
                        # Try to show JSON if from API, otherwise show raw text from library
                        if whois_data.get('raw_text') and whois_data.get('raw_text') != 'N/A':
                            st.text(whois_data['raw_text'])
                        else:
                            st.json(whois_data)
                        
                    success_checks.append("WHOIS lookup successful")
                        
                else:
                    st.warning("⚠️ Could not retrieve WHOIS information")
                    
                    # Fallback WHOIS links for manual checking (kept this helpful section)
                    st.info(f"""
                    **For .{tld} domains, try manual lookup at:**
                    """)
                    
                    ccTLD_registries = {
                        # African ccTLDs
                        'za': ('ZACR', 'https://www.registry.net.za/'),
                        'co.za': ('ZACR', 'https://www.registry.net.za/'),
                        'ng': ('NiRA', 'https://www.nira.org.ng/'),
                        'ke': ('KENIC', 'https://www.kenic.or.ke/'),
                        'tz': ('tzNIC', 'https://www.tznic.or.tz/'),
                        'gh': ('NIC Ghana', 'https://nic.gh/'),
                        'ug': ('UGENIC', 'https://www.registry.co.ug/'),
                        'rw': ('RICTA', 'https://www.ricta.org.rw/'),
                        'zw': ('ZISPA', 'https://www.zispa.co.zw/'),
                        'et': ('Ethio Telecom', 'https://www.ethiotelecom.et/'),
                        'zm': ('ZICTA', 'https://www.zicta.zm/'),
                        'ma': ('ANRT Morocco', 'https://www.registre.ma/'),
                        # Global TLDs
                        'us': ('Neustar', 'https://www.nic.us/'),
                        'eu': ('EURid', 'https://eurid.eu/'),
                        'uk': ('Nominet UK', 'https://www.nominet.uk/'),
                        'ca': ('CIRA', 'https://cira.ca/'),
                        'cn': ('CNNIC', 'https://www.cnnic.cn/')
                    }
                    
                    # Logic to find the TLD/2nd-level TLD for manual links
                    second_level_tld = '.'.join(domain.split('.')[-2:]).lower() if len(domain.split('.')) > 2 else None

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"[ICANN Lookup](https://lookup.icann.org/en/lookup?name={domain})")
                    with col2:
                        st.markdown(f"[Who.is](https://who.is/whois/{domain})")
                    with col3:
                        if second_level_tld and second_level_tld in ccTLD_registries:
                            registry_name, registry_url = ccTLD_registries[second_level_tld]
                            st.markdown(f"[{registry_name} Registry]({registry_url})")
                        elif tld in ccTLD_registries:
                            registry_name, registry_url = ccTLD_registries[tld]
                            st.markdown(f"[{registry_name} Registry]({registry_url})")
                        else:
                            st.markdown(f"[DomainTools](https://whois.domaintools.com/{domain})")
                    
                    if whois_raw:
                        with st.expander("📄 Raw WHOIS Output (Parsing Failed)"):
                            # Limit raw output length for better display
                            st.text(whois_raw[:2000] + ('...' if len(whois_raw) > 2000 else '')) 
                    
                    warnings.append("WHOIS data unavailable via automated tools")
                
                # 5. Summary Report (UNCHANGED)
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
                                
                    with st.expander("💡 Troubleshooting Tips"):
                        st.markdown("""
                        **Common Issues & Solutions:**
                        
                        **No Nameservers / Domain on Hold:**
                        - For .co.za domains: Complete COZA verification process
                        - Contact the Registrar to check for payment issues or mandatory verification.
                        
                        **WHOIS Retrieval Failed (ccTLDs):**
                        - The registry for this TLD likely requires special querying. Use the manual lookup links above.
                        
                        **DNS Resolution Failure (NXDOMAIN):**
                        - The domain is likely not registered, has expired, or is currently on registry hold. Check WHOIS dates.
                        """)

# Add placeholders for other tools if you plan to implement them
elif tool == "My IP":
    st.info("My IP Tool Coming Soon...")
elif tool == "IP Lookup":
    st.info("IP Lookup Tool Coming Soon...")
elif tool == "DNS Records":
    st.info("DNS Records Tool Coming Soon...")
elif tool == "SSL Check":
    st.info("SSL Check Tool Coming Soon...")
