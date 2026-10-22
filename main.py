__version__ = "1.0.0"
import json
from pathlib import Path
from datetime import date, timedelta
from kivy.app import App
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.progressbar import ProgressBar

BG=(.055,.075,.065,1); CARD=(.10,.13,.11,1); GREEN=(.25,.88,.48,1); WHITE=(.94,.97,.94,1); MUTED=(.64,.71,.66,1)
CATEGORIES={"Тренування":[],"Раціон":["Сніданок","Обід","Вечеря","Випити води"],"Навчання":["Виконати домашнє завдання","Повторити уроки","Повторити вивчене"],"Буденні справи":["Прибрати кімнату","Виконати особисті справи"]}
MEALS=["Сніданок","Обід","Вечеря","Перекус"]
def today(): return date.today().isoformat()
def fresh(): return {"day":today(),"tasks":{k:v[:] for k,v in CATEGORIES.items()},"checked":{},"daily_stats":{},"food":{},"water":{},"weight":"","height":"","weight_history":[],"height_history":[]}

class MyDay(App):
    title="Мій день"
    def build(self):
        Window.clearcolor=BG
        self.path=Path(self.user_data_dir)/"my_day.json"; self.path.parent.mkdir(parents=True,exist_ok=True)
        try: self.data=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception: self.data=fresh()
        for k,v in fresh().items(): self.data.setdefault(k,v)
        if self.data.get("day") != today():
            old=self.data.get("day")
            if old:
                total=sum(len(v) for v in self.data["tasks"].values())
                done=sum(1 for c,ts in self.data["tasks"].items() for t in ts if self.data["checked"].get(c,{}).get(t,False))
                self.data["daily_stats"][old]=round(done*100/total) if total else 0
            self.data["day"]=today(); self.data["checked"]={}
        root=BoxLayout(orientation="vertical",padding=dp(12),spacing=dp(8))
        head=BoxLayout(orientation="vertical",size_hint_y=None,height=dp(68))
        head.add_widget(self.label("МІЙ ДЕНЬ",24,GREEN,True)); head.add_widget(self.label(date.today().strftime("%d.%m.%Y")+" • твій план на день",12,MUTED)); root.add_widget(head)
        scroll=ScrollView(do_scroll_x=False); self.content=BoxLayout(orientation="vertical",spacing=dp(10),size_hint_y=None); self.content.bind(minimum_height=self.content.setter('height')); scroll.add_widget(self.content); root.add_widget(scroll)
        self.task_areas={}
        for cat in CATEGORIES: self.add_tasks_card(cat)
        self.add_food_card(); self.add_water_card(); self.add_body_card(); self.add_stats_card(); self.save(); self.refresh_all()
        return root
    def save(self):
        self.data["day"]=today(); self.path.write_text(json.dumps(self.data,ensure_ascii=False,indent=2),encoding="utf-8")
    def label(self,text,size=14,color=WHITE,bold=False):
        return Label(text=text,font_size=sp(size),color=color,bold=bold,halign='left',valign='middle',size_hint_y=None,height=dp(max(25,size*1.65)),text_size=(Window.width-dp(60),None))
    def button(self,text,fn,green=True):
        b=Button(text=text,size_hint_y=None,height=dp(42),font_size=sp(13),background_normal='',background_color=GREEN if green else (.19,.24,.20,1),color=(.04,.08,.05,1) if green else WHITE); b.bind(on_release=fn); return b
    def field(self,hint,text=''):
        return TextInput(text=text,hint_text=hint,multiline=False,size_hint_y=None,height=dp(43),padding=dp(9),font_size=sp(14),background_normal='',background_active='',background_color=(.15,.19,.16,1),foreground_color=WHITE,hint_text_color=MUTED,cursor_color=GREEN)
    def card(self,title):
        c=BoxLayout(orientation='vertical',spacing=dp(7),padding=dp(13),size_hint_y=None); c.bind(minimum_height=c.setter('height')); c.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle
        with c.canvas.before: Color(*CARD); c.bg=RoundedRectangle(pos=c.pos,size=c.size,radius=[dp(15)])
        c.bind(pos=lambda w,*a:setattr(w.bg,'pos',w.pos),size=lambda w,*a:setattr(w.bg,'size',w.size))
        c.add_widget(self.label(title,17,GREEN,True)); self.content.add_widget(c); return c
    def add_tasks_card(self,cat):
        c=self.card(cat); area=BoxLayout(orientation='vertical',spacing=dp(3),size_hint_y=None); area.bind(minimum_height=area.setter('height')); c.add_widget(area); self.task_areas[cat]=area
        inp=self.field('Введи нове завдання…'); c.add_widget(inp)
        def add(*a):
            name=inp.text.strip()
            if name and name not in self.data['tasks'][cat]: self.data['tasks'][cat].append(name); inp.text=''; self.save(); self.render_tasks(cat); self.refresh_stats()
        inp.bind(on_text_validate=add); c.add_widget(self.button('+ Додати завдання',add)); self.render_tasks(cat)
    def render_tasks(self,cat):
        area=self.task_areas[cat]; area.clear_widgets(); checks=self.data['checked'].setdefault(cat,{})
        for task in self.data['tasks'][cat]:
            row=BoxLayout(size_hint_y=None,height=dp(39),spacing=dp(4)); done=bool(checks.get(task,False))
            b=Button(text=('☑ ' if done else '□ ')+task,halign='left',font_size=sp(12),background_normal='',background_color=CARD,color=GREEN if done else WHITE); b.bind(on_release=lambda _,c=cat,t=task:self.toggle(c,t)); row.add_widget(b)
            x=Button(text='×',size_hint_x=None,width=dp(38),background_normal='',background_color=(.3,.15,.15,1),color=WHITE); x.bind(on_release=lambda _,c=cat,t=task:self.remove_task(c,t)); row.add_widget(x); area.add_widget(row)
    def toggle(self,cat,task):
        d=self.data['checked'].setdefault(cat,{}); d[task]=not d.get(task,False); self.save(); self.render_tasks(cat); self.refresh_stats()
    def remove_task(self,cat,task):
        if task in self.data['tasks'][cat]: self.data['tasks'][cat].remove(task)
        self.data['checked'].setdefault(cat,{}).pop(task,None); self.save(); self.render_tasks(cat); self.refresh_stats()
    def add_food_card(self):
        c=self.card('Раціон • щоденник їжі'); self.meal='Сніданок'; row=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(3)); self.meal_buttons=[]
        for meal in MEALS:
            b=Button(text=meal,font_size=sp(10),background_normal='',background_color=GREEN if meal==self.meal else (.19,.24,.20,1),color=(.04,.08,.05,1) if meal==self.meal else WHITE); b.bind(on_release=lambda _,m=meal:self.set_meal(m)); row.add_widget(b); self.meal_buttons.append(b)
        c.add_widget(row); self.food_name=self.field('Продукт або страва'); self.food_cal=self.field('Ккал, якщо відомо (необов’язково)'); c.add_widget(self.food_name); c.add_widget(self.food_cal); c.add_widget(self.button('Додати запис їжі',self.add_food)); self.food_summary=self.label('',12,MUTED); c.add_widget(self.food_summary); self.food_rows=BoxLayout(orientation='vertical',spacing=dp(3),size_hint_y=None); self.food_rows.bind(minimum_height=self.food_rows.setter('height')); c.add_widget(self.food_rows)
    def set_meal(self,m):
        self.meal=m
        for b in self.meal_buttons:
            sel=b.text==m; b.background_color=GREEN if sel else (.19,.24,.20,1); b.color=(.04,.08,.05,1) if sel else WHITE
    def add_food(self,*a):
        name=self.food_name.text.strip()
        if not name: return
        raw=self.food_cal.text.strip().replace(',','.'); cal=None
        if raw:
            try: cal=float(raw); assert cal>=0
            except Exception: self.food_summary.text='Ккал: введи число або залиш поле порожнім.'; return
        self.data['food'].setdefault(today(),[]).append({'meal':self.meal,'name':name,'calories':cal}); self.food_name.text=''; self.food_cal.text=''; self.save(); self.refresh_food()
    def refresh_food(self):
        if not hasattr(self,'food_rows'): return
        arr=self.data['food'].get(today(),[]); vals=[x['calories'] for x in arr if isinstance(x.get('calories'),(int,float))]; self.food_summary.text=f'Записів: {len(arr)} • Відомі значення: {sum(vals):.0f} ккал'; self.food_rows.clear_widgets()
        for i,it in enumerate(arr):
            cal='' if it.get('calories') is None else f" • {it['calories']:g} ккал"; row=BoxLayout(size_hint_y=None,height=dp(34)); row.add_widget(self.label(f"{it['meal']}: {it['name']}{cal}",11)); b=Button(text='×',size_hint_x=None,width=dp(36),background_normal='',background_color=(.3,.15,.15,1)); b.bind(on_release=lambda _,idx=i:self.delete_food(idx)); row.add_widget(b); self.food_rows.add_widget(row)
    def delete_food(self,i):
        a=self.data['food'].get(today(),[])
        if 0<=i<len(a): a.pop(i)
        self.save(); self.refresh_food()
    def add_water_card(self):
        c=self.card('Вода'); self.water_label=self.label('',14,WHITE,True); c.add_widget(self.water_label); row=BoxLayout(size_hint_y=None,height=dp(43),spacing=dp(6)); self.water_input=self.field('Об’єм у мл','250'); row.add_widget(self.water_input); row.add_widget(self.button('Додати',self.add_water)); c.add_widget(row); c.add_widget(self.button('Скасувати останній запис',self.undo_water,False))
    def add_water(self,*a):
        try: n=int(self.water_input.text.strip()); assert 1<=n<=5000
        except Exception: self.water_label.text='Введи об’єм від 1 до 5000 мл.'; return
        self.data['water'].setdefault(today(),[]).append(n); self.save(); self.refresh_water()
    def undo_water(self,*a):
        a=self.data['water'].get(today(),[])
        if a:a.pop()
        self.save(); self.refresh_water()
    def refresh_water(self):
        if hasattr(self,'water_label'): self.water_label.text=f"Записано сьогодні: {sum(self.data['water'].get(today(),[]))} мл"
    def add_body_card(self):
        c=self.card('Вага та зріст • історія'); self.weight_input=self.field('Вага у кг',str(self.data.get('weight',''))); self.height_input=self.field('Зріст у см',str(self.data.get('height',''))); c.add_widget(self.weight_input); c.add_widget(self.height_input); c.add_widget(self.button('Зберегти параметри',self.save_body)); c.add_widget(self.label('Записи необов’язкові. Додаток не встановлює ціль ваги.',11,MUTED)); self.body_history=self.label('',12); c.add_widget(self.body_history)
    def save_body(self,*a):
        try:
            wt=self.weight_input.text.strip().replace(',','.'); ht=self.height_input.text.strip().replace(',','.'); w=float(wt) if wt else None; h=float(ht) if ht else None
            if w is not None: assert 1<=w<=500
            if h is not None: assert 30<=h<=300
        except Exception: self.body_history.text='Перевір значення або залиш поле порожнім.'; return
        self.data['weight']=wt; self.data['height']=ht
        for key,val in [('weight_history',w),('height_history',h)]:
            if val is not None:
                hist=self.data[key]; rec={'date':today(),'value':val}
                if hist and hist[-1]['date']==today(): hist[-1]=rec
                else: hist.append(rec)
        self.save(); self.refresh_body()
    def refresh_body(self):
        if hasattr(self,'body_history'):
            hist=self.data['weight_history'][-5:]; self.body_history.text='Останні записи ваги:\n'+('\n'.join(f"{x['date']}: {x['value']:g} кг" for x in hist) if hist else 'Поки немає записів.')
    def calc_percent(self,day=None):
        day=day or today()
        if day in self.data.get('daily_stats',{}): return self.data['daily_stats'][day]
        if day!=today(): return 0
        total=sum(len(v) for v in self.data['tasks'].values()); done=sum(1 for c,ts in self.data['tasks'].items() for t in ts if self.data['checked'].get(c,{}).get(t,False)); return round(done*100/total) if total else 0
    def add_stats_card(self):
        c=self.card('Продуктивність'); self.percent_label=self.label('',22,GREEN,True); c.add_widget(self.percent_label); self.bar=ProgressBar(max=100,size_hint_y=None,height=dp(18)); c.add_widget(self.bar); self.count_label=self.label('',12,MUTED); c.add_widget(self.count_label); c.add_widget(self.label('Останні 7 днів',16,GREEN,True)); self.week_text=self.label('',12); c.add_widget(self.week_text); c.add_widget(self.button('Скинути всі галочки',self.reset_checks,False))
    def refresh_stats(self):
        if not hasattr(self,'bar'): return
        total=sum(len(v) for v in self.data['tasks'].values()); done=sum(1 for c,ts in self.data['tasks'].items() for t in ts if self.data['checked'].get(c,{}).get(t,False)); p=round(done*100/total) if total else 0; self.percent_label.text=f'{p}%'; self.bar.value=p; self.count_label.text=f'Виконано {done} із {total} завдань'; dates=[(date.today()-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]; self.week_text.text='\n'.join(f"{d[8:10]}.{d[5:7]} — {self.calc_percent(d)}%" for d in dates)
    def reset_checks(self,*a):
        self.data['daily_stats'][today()]=self.calc_percent(); self.data['checked']={}
        for cat in CATEGORIES:self.render_tasks(cat)
        self.save(); self.refresh_stats()
    def refresh_all(self): self.refresh_food(); self.refresh_water(); self.refresh_body(); self.refresh_stats()
if __name__=='__main__': MyDay().run()
