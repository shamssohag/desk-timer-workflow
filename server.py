import time
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'central_loop_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

timer_state = {
    'duration': 300,        # ৩০০ সেকেন্ড (৫ মিনিট)
    'time_left': 300,       
    'is_running': False,
    'current_step': 'social',
    'status_msg': 'Start your countdown.',
    'continuous_loop': True
}

def countdown_thread():
    global timer_state
    while True:
        if timer_state['is_running']:
            if timer_state['time_left'] > 0:
                time.sleep(1)
                if timer_state['is_running']:  
                    timer_state['time_left'] -= 1
            else:
                if timer_state['continuous_loop']:
                    duration = timer_state['duration']
                    timer_state['time_left'] = duration
                    if timer_state['current_step'] == 'social':
                        timer_state['current_step'] = 'web'
                        timer_state['status_msg'] = 'Continuous Loop: Social completed -> Web Timer Started!'
                    else:
                        timer_state['current_step'] = 'social'
                        timer_state['status_msg'] = 'Continuous Loop: Web completed -> Social Timer Started!'
                    timer_state['is_running'] = True
                else:
                    timer_state['is_running'] = False
                    if timer_state['current_step'] == 'social':
                        timer_state['status_msg'] = "Time's up! Social Team: Please post and click 'Social Post Done'."
                    else:
                        timer_state['status_msg'] = "Time's up! Web Team: Please post and click 'Web Post Done'."
                
                socketio.emit('update_timer', timer_state)
        else:
            time.sleep(0.5)
        
        if timer_state['is_running']:
            socketio.emit('update_timer', timer_state)

t = threading.Thread(target=countdown_thread, daemon=True)
t.start()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    emit('update_timer', timer_state)

@socketio.on('start_timer')
def handle_start():
    global timer_state
    if timer_state['time_left'] > 0:
        timer_state['is_running'] = True
        if timer_state['current_step'] == 'social':
            timer_state['status_msg'] = 'Social Loop Running...'
        else:
            timer_state['status_msg'] = 'Web Loop Running...'
        socketio.emit('update_timer', timer_state)

@socketio.on('pause_timer')
def handle_pause():
    global timer_state
    timer_state['is_running'] = False
    timer_state['status_msg'] = 'Timer Paused.'
    socketio.emit('update_timer', timer_state)

@socketio.on('reset_timer')
def handle_reset(data):
    global timer_state
    timer_state['is_running'] = False
    raw_duration = data.get('duration')
    duration = int(raw_duration) if raw_duration is not None else timer_state['duration']
    timer_state['duration'] = duration
    timer_state['time_left'] = duration
    timer_state['current_step'] = 'social'
  timer_state['current_step'] = 'social'
    timer_state['status_msg'] = 'Start your countdown.'
    socketio.emit('update_timer', timer_state)

@socketio.on('toggle_continuous')
def handle_toggle_continuous(data):
    global timer_state
    timer_state['continuous_loop'] = data.get('continuous_loop', True)
    socketio.emit('update_timer', timer_state)

@socketio.on('post_done')
def handle_post_done(data):
    global timer_state
    next_step = data.get('step')
    raw_duration = data.get('duration')
    duration = int(raw_duration) if raw_duration is not None else timer_state['duration']
    
    timer_state['is_running'] = True
    timer_state['duration'] = duration
    timer_state['time_`left`'] = duration # (এখানে ব্যাকটিক বা সাধারণ বানান ঠিক রাখা হয়েছে)
    timer_state['time_left'] = duration
    timer_state['current_step'] = next_step
    
    if next_step == 'web':
        timer_state['status_msg'] = 'Social Post Done! Web Countdown Started Automatically...'
    else:
        timer_state['status_msg'] = 'Web Post Done! Social Countdown Started Automatically...'
        
    socketio.emit('update_timer', timer_state)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
