# Smart Parking Management System 🚗

A Python-based Smart Parking Management System that automatically assigns the nearest available parking slot to incoming vehicles, tracks vehicle entry and exit, and calculates parking charges based on duration.

## Features

### 🎯 Core Features
- **Automatic Slot Allocation**: Greedy algorithm assigns the first available slot
- **Vehicle Entry Management**: Track vehicle entry with automatic slot assignment
- **Vehicle Exit Management**: Process exit with automatic fee calculation
- **Smart Fee Calculation**: ₹20 per hour with minimum charge of ₹20
- **Real-time Slot Status**: Visual representation of parking slot availability
- **Analytics Dashboard**: Comprehensive parking analytics with charts

### 📊 Dashboard Analytics
- Total parking slots overview
- Occupancy rate visualization
- Daily vehicle count
- Revenue tracking (daily & total)
- Parking duration distribution
- Recent parking history

## Technology Stack

- **Python**: Core programming language
- **Streamlit**: Web interface framework
- **Pandas**: Data handling and manipulation
- **Plotly**: Interactive charts and visualizations
- **JSON**: Slot status storage
- **CSV**: Vehicle records storage

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation Steps

1. **Clone/Download the project**
   ```bash
   cd "Parking Management"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

The application will automatically open in your web browser at `http://localhost:8501`

## Project Structure

```
smart_parking_system/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── slots.json         # Parking slot status storage
├── parking_data.csv   # Vehicle records storage
└── README.md          # Project documentation
```

## How to Use

### 1. Vehicle Entry
- Enter vehicle number (e.g., TN09AB1234)
- Select entry time (default: current time)
- Click "Assign Parking Slot"
- System automatically allocates the nearest available slot

### 2. Vehicle Exit
- Enter vehicle number
- Select exit time (default: current time)
- Click "Process Exit"
- System calculates duration and fee automatically
- Parking slot is freed for next vehicle

### 3. Slot Status
- View real-time parking slot availability
- Green (🟢) = Available
- Red (🔴) = Occupied
- See detailed slot information in table format

### 4. Analytics Dashboard
- Monitor occupancy rates
- Track revenue generation
- View parking duration statistics
- Access recent parking history

## Fee Calculation Logic

**Formula**: `Fee = ceil(hours_parked) × 20`

**Minimum Charge**: ₹20

**Example**:
- Entry Time: 10:00 AM
- Exit Time: 12:30 PM
- Duration: 2.5 hours → 3 hours (rounded up)
- Fee: 3 × 20 = ₹60

## Slot Allocation Algorithm

The system uses a **Greedy/First Available Slot Algorithm**:

1. Maintain ordered list of parking slots (P1-P10)
2. Check for first available slot
3. Assign slot to incoming vehicle
4. Mark slot as occupied
5. Free slot when vehicle exits

## Data Storage

### slots.json
Stores real-time parking slot status:
```json
{
    "P1": null,        // null = available
    "P2": "TN09AB1234", // vehicle number = occupied
    "P3": null,
    ...
}
```

### parking_data.csv
Stores complete vehicle history:
```csv
Vehicle,Slot,Entry_Time,Exit_Time,Duration_Hours,Fee
TN09AB1234,P1,2024-03-08 10:15:00,2024-03-08 12:30:00,2.25,60
```

## System Features

### 🎨 User Interface
- Clean, intuitive web interface
- Tabbed navigation for different functions
- Real-time updates without page refresh
- Responsive design for all screen sizes

### 📈 Analytics
- Interactive pie charts for occupancy visualization
- Histogram for parking duration analysis
- Real-time metrics display
- Historical data tracking

### 🔧 System Management
- Automatic data persistence
- Error handling for edge cases
- Input validation
- Refresh functionality

## Evaluation Points (Hackathon Ready)

✅ **Real-time slot allocation** - Automatic nearest slot assignment  
✅ **Automated parking management** - Complete entry/exit workflow  
✅ **Smart fee calculation** - Duration-based pricing with rounding  
✅ **Parking analytics dashboard** - Comprehensive metrics and charts  
✅ **User-friendly web interface** - Modern, intuitive Streamlit UI  

## Future Enhancements

- Multiple parking lot support
- Vehicle type-based pricing
- Employee/visitor differentiation
- SMS/email notifications
- Mobile app integration
- License plate recognition
- Payment gateway integration

## Troubleshooting

### Common Issues

1. **Port already in use**: Change port using `streamlit run app.py --server.port 8502`
2. **Dependencies not found**: Ensure virtual environment is activated
3. **File permissions**: Check read/write permissions for JSON/CSV files

### Support

For issues or questions, please check:
1. All dependencies are properly installed
2. Files have correct permissions
3. Python version is compatible

---

**Developed with ❤️ for Smart Parking Solutions**
