import streamlit as st
import pandas as pd
import json
import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

class ParkingManagementSystem:
    def __init__(self):
        self.slots_file = "slots.json"
        self.data_file = "parking_data.csv"
        self.fee_per_hour = 20
        self.min_fee = 20
        self.load_data()
    
    def load_data(self):
        try:
            with open(self.slots_file, 'r') as f:
                self.slots = json.load(f)
        except:
            self.slots = {
                "P1": None, "P2": None, "P3": None, "P4": None, "P5": None,
                "P6": None, "P7": None, "P8": None, "P9": None, "P10": None
            }
        
        try:
            self.parking_data = pd.read_csv(self.data_file)
        except:
            self.parking_data = pd.DataFrame(columns=['Vehicle', 'Slot', 'Entry_Time', 'Exit_Time', 'Duration_Hours', 'Fee'])
        
        # Synchronize slots with active vehicles
        self.synchronize_slots()
    
    def synchronize_slots(self):
        # Reset all slots to None
        for slot in self.slots:
            self.slots[slot] = None
        
        # Find active vehicles (those without exit time)
        active_vehicles = self.parking_data[self.parking_data['Exit_Time'].isin(['', 'nan', None]) | self.parking_data['Exit_Time'].isna()]
        
        # Update slots with active vehicles
        for _, row in active_vehicles.iterrows():
            if row['Slot'] in self.slots:
                self.slots[row['Slot']] = row['Vehicle']
        
        # Save synchronized data
        self.save_slot_data()
    
    def save_slot_data(self):
        with open(self.slots_file, 'w') as f:
            json.dump(self.slots, f, indent=4)
    
    def save_data(self):
        self.save_slot_data()
        self.parking_data.to_csv(self.data_file, index=False)
    
    def get_available_slots(self):
        return [slot for slot, vehicle in self.slots.items() if vehicle is None]
    
    def allocate_slot(self, vehicle_number):
        available_slots = self.get_available_slots()
        if not available_slots:
            return None
        
        allocated_slot = available_slots[0]
        self.slots[allocated_slot] = vehicle_number
        return allocated_slot
    
    def free_slot(self, slot):
        if slot in self.slots:
            self.slots[slot] = None
    
    def calculate_fee(self, entry_time, exit_time):
        duration = exit_time - entry_time
        hours = duration.total_seconds() / 3600
        billable_hours = max(1, int(hours) + (1 if hours % 1 > 0 else 0))
        fee = max(self.min_fee, billable_hours * self.fee_per_hour)
        return duration, hours, fee
    
    def vehicle_entry(self, vehicle_number, entry_time):
        allocated_slot = self.allocate_slot(vehicle_number)
        if allocated_slot:
            new_record = {
                'Vehicle': vehicle_number,
                'Slot': allocated_slot,
                'Entry_Time': entry_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Exit_Time': '',
                'Duration_Hours': 0,
                'Fee': 0
            }
            self.parking_data = pd.concat([self.parking_data, pd.DataFrame([new_record])], ignore_index=True)
            self.save_data()
            return allocated_slot
        return None
    
    def vehicle_exit(self, vehicle_number, exit_time):
        vehicle_records = self.parking_data[self.parking_data['Vehicle'] == vehicle_number]
        active_records = vehicle_records[vehicle_records['Exit_Time'] == '']
        
        if active_records.empty:
            return None
        
        idx = active_records.index[0]
        record = active_records.iloc[0]
        
        entry_time = datetime.datetime.strptime(record['Entry_Time'], '%Y-%m-%d %H:%M:%S')
        duration, hours, fee = self.calculate_fee(entry_time, exit_time)
        
        self.parking_data.loc[idx, 'Exit_Time'] = exit_time.strftime('%Y-%m-%d %H:%M:%S')
        self.parking_data.loc[idx, 'Duration_Hours'] = round(hours, 2)
        self.parking_data.loc[idx, 'Fee'] = fee
        
        self.free_slot(record['Slot'])
        self.save_data()
        
        return {
            'slot': record['Slot'],
            'duration': duration,
            'hours': hours,
            'fee': fee
        }
    
    def get_parking_stats(self):
        total_slots = len(self.slots)
        occupied_slots = sum(1 for vehicle in self.slots.values() if vehicle is not None)
        available_slots = total_slots - occupied_slots
        
        today = datetime.datetime.now().date()
        today_data = self.parking_data.copy()
        today_data['Entry_Date'] = pd.to_datetime(today_data['Entry_Time']).dt.date
        
        today_vehicles = today_data[today_data['Entry_Date'] == today]
        total_revenue = self.parking_data['Fee'].sum()
        today_revenue = today_vehicles['Fee'].sum()
        
        return {
            'total_slots': total_slots,
            'occupied_slots': occupied_slots,
            'available_slots': available_slots,
            'occupancy_rate': (occupied_slots / total_slots) * 100,
            'total_vehicles_today': len(today_vehicles),
            'total_revenue': total_revenue,
            'today_revenue': today_revenue
        }
    
    def get_duration_stats(self):
        completed_parking = self.parking_data[self.parking_data['Exit_Time'] != '']
        if completed_parking.empty:
            return pd.DataFrame()
        
        duration_stats = completed_parking['Duration_Hours'].describe()
        return duration_stats

def main():
    st.set_page_config(
        page_title="Smart Parking Management System",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(90deg, #3498db 0%, #2980b9 100%); border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; font-size: 2.5rem; margin: 0; font-weight: 700; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
            SMART PARKING MANAGEMENT SYSTEM
        </h1>
        <p style='color: #f0f0f0; font-size: 1.1rem; margin: 10px 0 0 0; font-weight: 300;'>
            Automated Slot Allocation & Real-time Parking Analytics🚗
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'parking_system' not in st.session_state:
        st.session_state.parking_system = ParkingManagementSystem()
    
    parking_system = st.session_state.parking_system
    
    # Custom CSS for interactive navigation tabs
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background-color: #1a1a1a;
            padding: 8px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.5);
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            white-space: pre-wrap;
            background-color: #2d2d2d;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 500;
            font-size: 14px;
            border: 1px solid #404040;
            transition: all 0.2s ease;
            cursor: pointer;
            position: relative;
            color: #e0e0e0;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(52, 152, 219, 0.25);
            border-color: #3498db;
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border-color: #2980b9;
            box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);
        }
        
        .stTabs [data-baseweb="tab"]:active {
            transform: translateY(0px);
            box-shadow: 0 1px 4px rgba(52, 152, 219, 0.2);
        }
        
        /* Icon animation */
        .stTabs [data-baseweb="tab"] span {
            transition: transform 0.15s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover span {
            transform: scale(1.05);
        }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["⬅️Vehicle Entry", "➡️Vehicle Exit", "🅿️Slot Status", "📊Analytics Dashboard"])
    
    with tab1:
        # Enhanced Header Section
        st.markdown("""
        <div style='background: radial-gradient(circle at 30% 70%, #3498db 0%, #2d2d2d 40%, #1a1a1a 100%); padding: 4px; border-radius: 15px; margin-bottom: 25px; border: 2px solid transparent; background-clip: padding-box; position: relative; overflow: hidden;'>
            <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(45deg, transparent 30%, rgba(52, 152, 219, 0.1) 50%, transparent 70%); pointer-events: none;'></div>
            <h3 style='color: #ffffff; margin: 0; font-size: 1.1rem; font-weight: 700; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3); position: relative; z-index: 1;'>
                🚗 Vehicle Entry
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            vehicle_number = st.text_input("Vehicle Number", placeholder="e.g., TN09AB1234")
            entry_date = st.date_input(
                "Entry Date",
                value=datetime.datetime.now().date()
            )
            entry_time_input = st.time_input(
                "Entry Time",
                value=datetime.datetime.now().time()
            )
            entry_time = datetime.datetime.combine(entry_date, entry_time_input)
        
        with col2:
            st.write("")
            st.write("")
            if st.button("Assign Parking Slot", type="primary", use_container_width=True):
                if vehicle_number:
                    allocated_slot = parking_system.vehicle_entry(vehicle_number, entry_time)
                    if allocated_slot:
                        st.success(f"✅ **Slot {allocated_slot} allocated successfully!**")
                        st.balloons()
                    else:
                        st.error("❌ No parking slots available!")
                else:
                    st.warning("⚠️ Please enter vehicle number")
    
    with tab2:
        # Enhanced Header Section
        st.markdown("""
        <div style='background: radial-gradient(circle at 70% 30%, #ff9f43 0%, #2d2d2d 40%, #1a1a1a 100%); padding: 4px; border-radius: 15px; margin-bottom: 25px; border: 2px solid transparent; background-clip: padding-box; position: relative; overflow: hidden;'>
            <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(135deg, transparent 30%, rgba(255, 159, 67, 0.1) 50%, transparent 70%); pointer-events: none;'></div>
            <h3 style='color: #ffffff; margin: 0; font-size: 1.1rem; font-weight: 700; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3); position: relative; z-index: 1;'>
                🚙 Vehicle Exit
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            exit_vehicle_number = st.text_input("Vehicle Number", key="exit_vehicle", placeholder="e.g., TN09AB1234")
            exit_date = st.date_input(
                "Exit Date",
                value=datetime.datetime.now().date(),
                key="exit_date"
            )
            exit_time_input = st.time_input(
                "Exit Time",
                value=datetime.datetime.now().time(),
                key="exit_time_input"
            )
            exit_time = datetime.datetime.combine(exit_date, exit_time_input)
        
        with col2:
            st.write("")
            st.write("")
            if st.button("Process Exit", type="primary", use_container_width=True):
                if exit_vehicle_number:
                    exit_result = parking_system.vehicle_exit(exit_vehicle_number, exit_time)
                    if exit_result:
                        st.success(f"✅ **Exit processed successfully!**")
                        st.info(f"**Slot Released:** {exit_result['slot']}")
                        st.info(f"**Parking Duration:** {exit_result['hours']:.1f} hours")
                        st.info(f"**Parking Fee:** ₹{exit_result['fee']}")
                    else:
                        st.error("❌ Vehicle not found or already exited!")
                else:
                    st.warning("⚠️ Please enter vehicle number")
    
    with tab3:
        # Create slots dataframe for table display
        slots_display = []
        for slot, vehicle in parking_system.slots.items():
            status = "🔴 Occupied" if vehicle else "🟢 Available"
            vehicle_info = f"({vehicle})" if vehicle else ""
            slots_display.append({
                'Slot': slot,
                'Status': status,
                'Vehicle': vehicle_info
            })
        
        slots_df = pd.DataFrame(slots_display)
        
        # Enhanced Header Section
        st.markdown("""
        <div style='background: radial-gradient(circle at 20% 80%, #3498db 0%, #2d2d2d 50%, #1a1a1a 100%); padding: 4px; border-radius: 15px; margin-bottom: 25px; border: 2px solid transparent; background-clip: padding-box; position: relative; overflow: hidden;'>
            <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(45deg, transparent 30%, rgba(52, 152, 219, 0.1) 50%, transparent 70%); pointer-events: none;'></div>
            <h3 style='color: #ffffff; margin: 0; font-size: 1.1rem; font-weight: 700; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3); position: relative; z-index: 1;'>
                🖥️Real-time Parking Slot Monitor
            </h3>
            <p style='color: #f0f0f0; margin: 3px 0 0 0; text-align: center; font-size: 0.75rem; font-weight: 400; text-shadow: 0 1px 2px rgba(0,0,0,0.2); position: relative; z-index: 1;'>
                Live slot availability and vehicle tracking
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced Metrics Cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style='background-color: #2d2d2d; padding: 15px; border-radius: 8px; border: 1px solid #404040; text-align: center;'>
                <h4 style='color: #3498db; margin: 0 0 8px 0; font-size: 0.9rem;'>TOTAL SLOTS</h4>
                <p style='color: white; margin: 0; font-size: 1.8rem; font-weight: 700;'>{}</p>
            </div>
            """.format(len(parking_system.slots)), unsafe_allow_html=True)
        
        with col2:
            occupied = sum(1 for v in parking_system.slots.values() if v)
            st.markdown("""
            <div style='background-color: #2d2d2d; padding: 15px; border-radius: 8px; border: 1px solid #404040; text-align: center;'>
                <h4 style='color: #ff6b6b; margin: 0 0 8px 0; font-size: 0.9rem;'>OCCUPIED</h4>
                <p style='color: white; margin: 0; font-size: 1.8rem; font-weight: 700;'>{}</p>
            </div>
            """.format(occupied), unsafe_allow_html=True)
        
        with col3:
            available = len(parking_system.slots) - occupied
            st.markdown("""
            <div style='background-color: #2d2d2d; padding: 15px; border-radius: 8px; border: 1px solid #404040; text-align: center;'>
                <h4 style='color: #51cf66; margin: 0 0 8px 0; font-size: 0.9rem;'>AVAILABLE</h4>
                <p style='color: white; margin: 0; font-size: 1.8rem; font-weight: 700;'>{}</p>
            </div>
            """.format(available), unsafe_allow_html=True)
        
        # Enhanced Parking Layout Section
        st.markdown("""
        <div style='background: radial-gradient(ellipse at 10% 90%, #2d2d2d 0%, #1a1a1a 100%); padding: 3px; border-radius: 12px; margin: 20px 0; border: 2px solid transparent; background-image: linear-gradient(#1a1a1a, #1a1a1a), linear-gradient(45deg, #3498db, #2980b9); background-origin: border-box; background-clip: padding-box, border-box; position: relative;'>
            <div style='position: absolute; top: -2px; left: -2px; right: -2px; bottom: -2px; background: linear-gradient(45deg, #3498db, #2980b9, #3498db); border-radius: 12px; z-index: -1;'></div>
            <h3 style='color: #ffffff; margin: 0; font-size: 0.9rem; font-weight: 600; text-align: center; text-shadow: 0 1px 3px rgba(0,0,0,0.4);'>
                🅿️ Interactive Parking Layout
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced Slot Grid with better styling
        cols = st.columns(5)
        for i, (slot, vehicle) in enumerate(parking_system.slots.items()):
            col_idx = i % 5
            with cols[col_idx]:
                if vehicle:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); padding: 15px; border-radius: 8px; text-align: center; border: 2px solid #ff6b6b; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);'>
                        <h4 style='color: white; margin: 0; font-size: 1rem; font-weight: 700;'>{slot}</h4>
                        <p style='color: white; margin: 5px 0 0 0; font-size: 0.8rem;'>🔴 OCCUPIED</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"<p style='color: #e0e0e0; text-align: center; margin: 0 0 15px 0; font-size: 0.8rem; background-color: #2d2d2d; padding: 5px; border-radius: 4px;'>{vehicle}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #51cf66 0%, #40c057 100%); padding: 15px; border-radius: 8px; text-align: center; border: 2px solid #51cf66; margin-bottom: 10px; box-shadow: 0 2px 8px rgba(81, 207, 102, 0.3);'>
                        <h4 style='color: white; margin: 0; font-size: 1rem; font-weight: 700;'>{slot}</h4>
                        <p style='color: white; margin: 5px 0 0 0; font-size: 0.8rem;'>🟢 AVAILABLE</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<p style='color: #b0b0b0; text-align: center; margin: 0 0 15px 0; font-size: 0.8rem; background-color: #2d2d2d; padding: 5px; border-radius: 4px;'>Available</p>", unsafe_allow_html=True)
        
        # Enhanced Table Section Header
        st.markdown("""
        <div style='background: conic-gradient(from 180deg at 50% 50%, #2d2d2d 0deg, #3498db 90deg, #2d2d2d 180deg, #2980b9 270deg, #2d2d2d 360deg); padding: 1px; border-radius: 12px; margin: 20px 0;'>
            <div style='background: #1a1a1a; padding: 4px; border-radius: 10px; border: 1px solid rgba(52, 152, 219, 0.3);'>
                <h3 style='color: #3498db; margin: 0; font-size: 0.9rem; font-weight: 600; text-align: center; text-shadow: 0 0 10px rgba(52, 152, 219, 0.5);'>
                    📊 Detailed Slot Information
                </h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Keep the tabular format unchanged as requested
        st.dataframe(slots_df, use_container_width=True, hide_index=True)
    
    with tab4:
        # Enhanced Header Section
        st.markdown("""
        <div style='background: radial-gradient(circle at 80% 20%, #3498db 0%, #2d2d2d 40%, #1a1a1a 100%); padding: 4px; border-radius: 15px; margin-bottom: 25px; border: 2px solid transparent; background-clip: padding-box; position: relative; overflow: hidden;'>
            <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(135deg, transparent 40%, rgba(52, 152, 219, 0.15) 60%, transparent 80%); pointer-events: none;'></div>
            <h3 style='color: #ffffff; margin: 0; font-size: 1.1rem; font-weight: 700; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3); position: relative; z-index: 1;'>
                📊 Analytics Dashboard
            </h3>
            <p style='color: #f0f0f0; margin: 3px 0 0 0; text-align: center; font-size: 0.75rem; font-weight: 400; text-shadow: 0 1px 2px rgba(0,0,0,0.2); position: relative; z-index: 1;'>
                Comprehensive parking analytics and insights
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        stats = parking_system.get_parking_stats()
        
        # Key Metrics Section
        st.markdown("### 📈 Key Performance Metrics")
        
        # Enhanced Metrics Cards
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #3498db; box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 500;'>OCCUPANCY RATE</h4>
                <p style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>{:.1f}%</p>
            </div>
            """.format(stats['occupancy_rate']), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #51cf66 0%, #40c057 100%); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #51cf66; box-shadow: 0 2px 8px rgba(81, 207, 102, 0.3);'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 500;'>VEHICLES TODAY</h4>
                <p style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>{}</p>
            </div>
            """.format(stats['total_vehicles_today']), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #ff9f43 0%, #ff6b6b 100%); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ff9f43; box-shadow: 0 2px 8px rgba(255, 159, 67, 0.3);'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 500;'>TODAY'S REVENUE</h4>
                <p style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>₹{}</p>
            </div>
            """.format(stats['today_revenue']), unsafe_allow_html=True)
        
        with col4:
            total_vehicles = len(parking_system.parking_data)
            st.markdown("""
            <div style='background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #9b59b6; box-shadow: 0 2px 8px rgba(155, 89, 182, 0.3);'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 500;'>TOTAL VEHICLES</h4>
                <p style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>{}</p>
            </div>
            """.format(total_vehicles), unsafe_allow_html=True)
        
        with col5:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #00d2d3 0%, #00a8cc 100%); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #00d2d3; box-shadow: 0 2px 8px rgba(0, 210, 211, 0.3);'>
                <h4 style='color: white; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 500;'>TOTAL REVENUE</h4>
                <p style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>₹{}</p>
            </div>
            """.format(stats['total_revenue']), unsafe_allow_html=True)
        
        # Charts Section
        st.markdown("### 📊 Visual Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Occupied', 'Available'],
                values=[stats['occupied_slots'], stats['available_slots']],
                hole=0.4,
                marker_colors=['#FF6B6B', '#4ECDC4']
            )])
            fig_pie.update_layout(
                title="Parking Occupancy Distribution",
                font=dict(size=14)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            completed_parking = parking_system.parking_data[parking_system.parking_data['Exit_Time'] != '']
            
            if not completed_parking.empty:
                fig_duration = px.histogram(
                    completed_parking,
                    x='Duration_Hours',
                    nbins=10,
                    title="Parking Duration Distribution",
                    color_discrete_sequence=['#45B7D1']
                )
                fig_duration.update_layout(
                    xaxis_title="Duration (Hours)",
                    yaxis_title="Number of Vehicles"
                )
                st.plotly_chart(fig_duration, use_container_width=True)
            else:
                st.info("No parking duration data available yet")
        
        # Enhanced Recent History Section
        if not parking_system.parking_data.empty:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a1a 100%); padding: 4px; border-radius: 12px; margin: 20px 0; border: 2px solid #3498db; box-shadow: 0 0 20px rgba(52, 152, 219, 0.2), inset 0 0 20px rgba(52, 152, 219, 0.05); position: relative;'>
                <div style='position: absolute; top: 0; left: 0; right: 0; height: 1px; background: linear-gradient(90deg, transparent, #3498db, transparent);'></div>
                <h3 style='color: #3498db; margin: 0; font-size: 0.9rem; font-weight: 600; text-align: center; text-shadow: 0 0 8px rgba(52, 152, 219, 0.6);'>
                    📋 Recent Parking History
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            recent_data = parking_system.parking_data.tail(10).copy()
            recent_data = recent_data[::-1]
            
            # Format the duration display
            def format_duration(duration_hours):
                if duration_hours == 0:
                    return "In Progress"
                else:
                    hours = int(duration_hours)
                    minutes = int((duration_hours - hours) * 60)
                    if hours > 0 and minutes > 0:
                        return f"{hours}h {minutes}m"
                    elif hours > 0:
                        return f"{hours}h"
                    else:
                        return f"{minutes}m"
            
            recent_data['Duration'] = recent_data['Duration_Hours'].apply(format_duration)
            # Keep tabular format unchanged as requested
            st.dataframe(recent_data[['Vehicle', 'Slot', 'Entry_Time', 'Exit_Time', 'Duration', 'Fee']], 
                         use_container_width=True, hide_index=True)
            
            # Enhanced Day-wise Revenue Section
            st.markdown("""
            <div style='background: radial-gradient(circle at 90% 10%, #3498db 0%, #2d2d2d 30%, #1a1a1a 100%); padding: 4px; border-radius: 12px; margin: 20px 0; border: 2px solid transparent; background-clip: padding-box; position: relative; overflow: hidden;'>
                <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(45deg, transparent 30%, rgba(52, 152, 219, 0.1) 50%, transparent 70%); pointer-events: none;'></div>
                <h3 style='color: #ffffff; margin: 0; font-size: 0.9rem; font-weight: 600; text-align: center; text-shadow: 0 2px 4px rgba(0,0,0,0.3); position: relative; z-index: 1;'>
                    📈 Day-wise Revenue Analysis
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Process data for day-wise analysis
            if not parking_system.parking_data.empty:
                # Convert Entry_Time to datetime
                parking_system.parking_data['Entry_Date'] = pd.to_datetime(parking_system.parking_data['Entry_Time']).dt.date
                
                # Group by date and calculate metrics
                daily_stats = parking_system.parking_data.groupby('Entry_Date').agg({
                    'Vehicle': 'count',  # Count of vehicles
                    'Fee': 'sum'         # Total revenue
                }).reset_index()
                
                # Rename columns
                daily_stats.columns = ['Date', 'Vehicles_Parked', 'Revenue']
                
                # Format date and revenue
                daily_stats['Date'] = pd.to_datetime(daily_stats['Date']).dt.strftime('%Y-%m-%d')
                daily_stats['Revenue'] = daily_stats['Revenue'].apply(lambda x: f"₹{x}")
                
                # Sort by date (newest first)
                daily_stats = daily_stats.sort_values('Date', ascending=False)
                
                # Keep tabular format unchanged as requested
                st.dataframe(daily_stats, use_container_width=True, hide_index=True)
                
                # Enhanced Summary Statistics
                st.markdown("""
                <div style='background: linear-gradient(45deg, #1a1a1a 25%, #2d2d2d 50%, #1a1a1a 75%); padding: 4px; border-radius: 12px; margin: 20px 0; border: 2px solid #3498db; position: relative; overflow: hidden;'>
                    <div style='position: absolute; top: 0; left: -100%; width: 200%; height: 100%; background: linear-gradient(90deg, transparent, rgba(52, 152, 219, 0.3), transparent); animation: shimmer 3s infinite;'></div>
                    <h3 style='color: #3498db; margin: 0; font-size: 0.9rem; font-weight: 600; text-align: center; text-shadow: 0 0 10px rgba(52, 152, 219, 0.8); position: relative; z-index: 1;'>
                        📊 Summary Statistics
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Summary statistics
                total_days = len(daily_stats)
                avg_vehicles = daily_stats['Vehicles_Parked'].mean()
                avg_revenue = parking_system.parking_data['Fee'].sum() / total_days if total_days > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #3498db; box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3);'>
                        <h4 style='color: white; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 500;'>TOTAL DAYS</h4>
                        <p style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>{}</p>
                    </div>
                    """.format(total_days), unsafe_allow_html=True)
                with col2:
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, #51cf66 0%, #40c057 100%); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #51cf66; box-shadow: 0 2px 8px rgba(81, 207, 102, 0.3);'>
                        <h4 style='color: white; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 500;'>AVG VEHICLES/DAY</h4>
                        <p style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>{:.1f}</p>
                    </div>
                    """.format(avg_vehicles), unsafe_allow_html=True)
                with col3:
                    st.markdown("""
                    <div style='background: linear-gradient(135deg, #ff9f43 0%, #ff6b6b 100%); padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #ff9f43; box-shadow: 0 2px 8px rgba(255, 159, 67, 0.3);'>
                        <h4 style='color: white; margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 500;'>AVG REVENUE/DAY</h4>
                        <p style='color: white; margin: 0; font-size: 1.5rem; font-weight: 700;'>₹{:.0f}</p>
                    </div>
                    """.format(avg_revenue), unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style='background-color: #2d2d2d; padding: 20px; border-radius: 8px; border: 1px solid #404040; text-align: center;'>
                    <p style='color: #e0e0e0; margin: 0; font-size: 1rem;'>No parking data available for day-wise analysis</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Enhanced Sidebar Styling
    st.markdown("""
    <style>
        .css-1d391kg {
            background-color: #1a1a1a !important;
        }
        .css-17eq0hr {
            background-color: #1a1a1a !important;
        }
        .css-1lcbmhc {
            background-color: #1a1a1a !important;
        }
        .css-1outpf7 {
            background-color: #1a1a1a !important;
        }
        .css-1v0mbdj {
            background-color: #1a1a1a !important;
        }
        .css-1r6slb0 {
            background-color: #1a1a1a !important;
        }
        .css-1avcm0n {
            background-color: #1a1a1a !important;
        }
        .css-1d391kg, .css-17eq0hr, .css-1lcbmhc, .css-1outpf7, .css-1v0mbdj, .css-1r6slb0, .css-1avcm0n {
            color: #e0e0e0 !important;
        }
        .css-1d391kg .css-17eq0hr {
            border-right: 1px solid #333333 !important;
        }
        
        /* Change primary button colors to light blue */
        .stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #3498db 0%, #2980b9 100%) !important;
            border: 1px solid #3498db !important;
            color: white !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button[kind="primary"]:hover {
            background: linear-gradient(90deg, #2980b9 0%, #3498db 100%) !important;
            border-color: #2980b9 !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 2px 8px rgba(52, 152, 219, 0.3) !important;
        }
        
        .stButton > button[kind="primary"]:active {
            transform: translateY(0px) !important;
            box-shadow: 0 1px 4px rgba(52, 152, 219, 0.2) !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar Header
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 20px 10px; background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%); border-radius: 10px; margin-bottom: 20px; border: 1px solid #404040;'>
            <h2 style='color: #3498db; font-size: 1.5rem; margin: 0; font-weight: 700;'>
                CONTROL PANEL
            </h2>
            <p style='color: #e0e0e0; font-size: 0.9rem; margin: 5px 0 0 0; font-weight: 300;'>
                System Management
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick Stats
        st.markdown("### 📊 Quick Stats")
        stats = parking_system.get_parking_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="🅿️Available Slots", 
                value=f"{stats['available_slots']}/{stats['total_slots']}",
                delta=f"{stats['occupancy_rate']:.0f}%"
            )
        with col2:
            st.metric(
                label="💰 Today Revenue", 
                value=f"₹{stats['today_revenue']}"
            )
        
        # Add Total Revenue below
        st.markdown("### 💰 Total Revenue")
        st.metric(
            label="Total Revenue", 
            value=f"₹{stats['total_revenue']}"
        )
        
        st.markdown("---")
        
        # System Information
        st.markdown("### ⚙️ System Configuration")
        
        # Fee Information Card
        st.markdown("""
        <div style='background-color: #2d2d2d; padding: 15px; border-radius: 8px; border: 1px solid #404040; margin-bottom: 15px;'>
            <h4 style='color: #3498db; margin: 0 0 10px 0; font-size: 1rem;'>💳 Fee Structure</h4>
            <p style='color: #e0e0e0; margin: 5px 0; font-size: 0.9rem;'>
                <strong>Rate:</strong> ₹{}/hour<br>
                <strong>Minimum:</strong> ₹{}/hour
            </p>
        </div>
        """.format(parking_system.fee_per_hour, parking_system.min_fee), unsafe_allow_html=True)
        
        # Time Information
        current_time = datetime.datetime.now()
        st.markdown("""
        <div style='background-color: #2d2d2d; padding: 15px; border-radius: 8px; border: 1px solid #404040; margin-bottom: 15px;'>
            <h4 style='color: #3498db; margin: 0 0 10px 0; font-size: 1rem;'>🕐 Current Time</h4>
            <p style='color: #e0e0e0; margin: 5px 0; font-size: 0.9rem;'>
                <strong>Date:</strong> {}<br>
                <strong>Time:</strong> {}
            </p>
        </div>
        """.format(current_time.strftime('%Y-%m-%d'), current_time.strftime('%H:%M:%S')), unsafe_allow_html=True)
        
        # Action Buttons
        st.markdown("### 🎯 Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True, help="Refresh all data"):
                parking_system.load_data()
                st.rerun()
        
        with col2:
            if st.button("📈Stats", use_container_width=True, help="View detailed statistics"):
                st.success("Navigate to 📊Analytics Dashboard tab for detailed statistics!")
        
        # System Status
        st.markdown("---")
        st.markdown("### 🟢 System Status")
        
        # Determine status based on occupancy
        if stats['occupancy_rate'] < 50:
            status_color = "#00ff00"
            status_text = "Low Traffic"
        elif stats['occupancy_rate'] < 80:
            status_color = "#ffaa00"
            status_text = "Moderate Traffic"
        else:
            status_color = "#3498db"
            status_text = "High Traffic"
        
        st.markdown("""
        <div style='background-color: #2d2d2d; padding: 15px; border-radius: 8px; border: 1px solid #404040; text-align: center;'>
            <div style='width: 12px; height: 12px; background-color: {}; border-radius: 50%; display: inline-block; margin-right: 8px; animation: pulse 2s infinite;'></div>
            <span style='color: #e0e0e0; font-weight: 600;'>{}</span>
            <p style='color: #b0b0b0; margin: 8px 0 0 0; font-size: 0.8rem;'>{} slots occupied</p>
        </div>
        <style>
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        </style>
        """.format(status_color, status_text, stats['occupied_slots']), unsafe_allow_html=True)
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; padding: 10px; color: #808080; font-size: 0.8rem;'>
            <p>🚗 Smart Parking v1.0</p>
            <p>Powered by Streamlit</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
