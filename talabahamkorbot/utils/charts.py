
import io
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict

# Set style
sns.set_theme(style="whitegrid")

def generate_faculty_stats_chart(data: Dict[str, int]) -> io.BytesIO:
    """
    Generates a pie chart for faculty student distribution.
    data format: {"Fakultet A": 100, "Fakultet B": 200}
    """
    plt.figure(figsize=(10, 6))
    
    labels = list(data.keys())
    values = list(data.values())
    
    # Create pie chart
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=sns.color_palette("pastel"))
    plt.title("Talabalar Taqsimoti (Fakultetlar kesimida)")
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generate_activity_stats_chart(confirmed: int, rejected: int, pending: int) -> io.BytesIO:
    """
    Generates a bar chart for activity status.
    """
    plt.figure(figsize=(8, 5))
    
    categories = ['Tasdiqlangan', 'Rad etilgan', 'Kutilmoqda']
    values = [confirmed, rejected, pending]
    colors = ['#2ecc71', '#e74c3c', '#f1c40f'] # Green, Red, Yellow
    
    sns.barplot(x=categories, y=values, palette=colors)
    plt.title("Faolliklar Statistikasi")
    plt.ylabel("Soni")
    
    # Add value labels on top of bars
    for i, v in enumerate(values):
        plt.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
    
    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf
