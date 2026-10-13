package com.pinedaagencygroup.leads;

import android.app.*;
import android.graphics.Color;
import android.content.Intent;
import android.net.Uri;
import android.text.InputType;
import android.view.*;
import android.widget.*;
import com.google.firebase.auth.*;
import com.google.firebase.firestore.*;
import com.google.firebase.Timestamp;
import org.json.JSONObject;
import java.util.*;

/** Native owner/agent workspace. Prospect data is held in memory only. */
final class AgentWorkspace {
    private static final int NAVY=Color.rgb(11,29,50), GOLD=Color.rgb(200,154,61);
    private static final String[] STATUSES={"Nuevo","Contactado","Cita","Seguimiento","Completado"};
    private final Activity activity;
    private final AgentStore store=new AgentStore();
    private final String uid;
    private final boolean owner, clients, recruitment;
    private final Runnable legacy;
    private final LinearLayout root, body;
    private final List<ListenerRegistration> watches=new ArrayList<>();
    private int generation;
    private boolean closed;
    private TextView message;
    private AlertDialog dialog;

    AgentWorkspace(Activity activity, DocumentSnapshot profile, Runnable legacy) {
        this.activity=activity;this.legacy=legacy;uid=profile.getId();owner="owner".equals(profile.getString("role"));
        clients=owner||Boolean.TRUE.equals(profile.get("scopes.clients"));
        recruitment=owner||Boolean.TRUE.equals(profile.get("scopes.recruitment"));
        root=new LinearLayout(activity);root.setOrientation(1);root.setBackgroundColor(Color.rgb(247,243,234));
        TextView brand=new TextView(activity);brand.setText("Pineda Agency Group\nPineda Insurance Group · v1.9 PRUEBA QA2");brand.setTextColor(Color.WHITE);brand.setTextSize(18);brand.setPadding(24,20,24,20);brand.setBackgroundColor(NAVY);root.addView(brand);
        ScrollView scroll=new ScrollView(activity);body=new LinearLayout(activity);body.setOrientation(1);body.setPadding(24,12,24,28);scroll.setFillViewport(true);scroll.addView(body);root.addView(scroll);
        home();
    }
    View view(){return root;}
    void close(){closed=true;clear();body.removeAllViews();}
    private void clear(){generation++;for(ListenerRegistration l:watches)l.remove();watches.clear();if(dialog!=null)dialog.dismiss();dialog=null;}
    private boolean current(int ticket){FirebaseUser u=FirebaseAuth.getInstance().getCurrentUser();return !closed&&ticket==generation&&u!=null&&uid.equals(u.getUid())&&!activity.isDestroyed();}
    private int screen(String title){clear();body.removeAllViews();TextView h=text(title,23);h.setTextColor(NAVY);message=text("",14);return generation;}
    private TextView text(String value,int size){TextView t=new TextView(activity);t.setText(value);t.setTextSize(size);t.setTextColor(NAVY);t.setPadding(0,12,0,8);body.addView(t);return t;}
    private Button button(String label,Runnable action){Button b=new Button(activity);b.setText(label);b.setTextColor(NAVY);b.setAllCaps(false);body.addView(b);b.setOnClickListener(v->action.run());return b;}
    private EditText field(String label,String value,boolean multiline,int max){text(label,14);EditText e=new EditText(activity);e.setText(value);e.setTextSize(16);e.setSaveEnabled(false);e.setSingleLine(!multiline);e.setInputType(InputType.TYPE_CLASS_TEXT|(multiline?InputType.TYPE_TEXT_FLAG_MULTI_LINE:0));e.setFilters(new android.text.InputFilter[]{new android.text.InputFilter.LengthFilter(max)});if(multiline)e.setMinLines(3);body.addView(e);return e;}
    private CheckBox check(String label,boolean checked){CheckBox c=new CheckBox(activity);c.setText(label);c.setChecked(checked);body.addView(c);return c;}
    private Spinner select(String label,String[] values,String selected){text(label,14);Spinner s=new Spinner(activity);ArrayAdapter<String>a=new ArrayAdapter<>(activity,android.R.layout.simple_spinner_dropdown_item,values);s.setAdapter(a);for(int i=0;i<values.length;i++)if(values[i].equals(selected))s.setSelection(i);body.addView(s);return s;}
    private String value(DocumentSnapshot d,String key){String s=d.getString(key);return s==null?"":s;}
    private String input(EditText e){return e.getText().toString().trim();}
    private void error(Exception e){message.setText(AgentStore.conflict(e)?"Otro teléfono cambió este registro. Tu edición sigue aquí; vuelve a abrirlo para revisar la versión actual antes de guardar.":"No se pudo completar. Revisa tu conexión y permisos; no se confirmó ningún cambio.");}
    private void back(){button("Volver al inicio",this::home);}
    void home(){screen(owner?"Administrar mi equipo":"Mis prospectos");text(owner?"Aprueba accesos y asigna prospectos a cada agente.":"Aquí aparecen solo las secciones autorizadas y los prospectos que Juan te asignó.",16);
        if(owner)button("Solicitudes y agentes",()->accounts(null));
        if(clients)button("Clientes Final Expense",()->records("clients",null));
        if(recruitment)button("Reclutamiento asignado",()->records("recruitmentAssignments",null));
        if(!clients&&!recruitment)text("Tu acceso está aprobado, pero aún no tienes secciones habilitadas.",16);
        if(owner)button("Mi base original de reclutamiento",legacy);
        if(!owner) {
            button("Preferencias de avisos",this::notificationSettings);
            String device=activity.getSharedPreferences("pag_native",0).getString("firebase_device_id","");
            if(device.length()>=4)text("Este teléfono: "+device.substring(device.length()-4)+" · Juan debe aprobarlo para recibir avisos.",14);
        }
        button("Cerrar sesión",()->{close();FirebaseAuth.getInstance().signOut();});
    }
    private void accounts(DocumentSnapshot cursor){int ticket=screen("Solicitudes y agentes");back();text("Abre un correo para aprobar, cambiar permisos, suspender o rechazar el acceso.",15);
        Query q=store.db.collection("accessRequests").orderBy(FieldPath.documentId()).limit(50);if(cursor!=null)q=q.startAfter(cursor);
        q.get(Source.SERVER).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(!t.isSuccessful()){error(t.getException());return;}
            if(t.getResult().isEmpty())text("No hay solicitudes en esta página.",16);
            for(DocumentSnapshot d:t.getResult()){Button row=button(value(d,"name")+"\n"+value(d,"email")+" · Consultando…",()->account(d));
                store.db.collection("users").document(d.getId()).get(Source.SERVER).addOnSuccessListener(activity,p->{if(!current(ticket))return;String state=!p.exists()?"Pendiente":Boolean.TRUE.equals(p.getBoolean("suspended"))?"Suspendido":Boolean.TRUE.equals(p.getBoolean("active"))?"Aprobado":"Sin acceso";row.setText(value(d,"name")+"\n"+value(d,"email")+" · "+state);});
            }
            if(t.getResult().size()==50)button("Siguiente página",()->accounts(t.getResult().getDocuments().get(49)));
            if(cursor!=null)button("Primera página",()->accounts(null));
        });
    }
    private void account(DocumentSnapshot request){int ticket=screen("Autorizar agente");back();
        store.db.collection("users").document(request.getId()).get(Source.SERVER).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(!t.isSuccessful()){error(t.getException());return;}
            DocumentSnapshot p=t.getResult();if(p.exists()&&!"agent".equals(p.getString("role"))){message.setText("Este perfil no puede modificarse aquí.");return;}
            text(value(request,"email"),18);text("Correo verificado al solicitar. Cada permiso se aplica únicamente a los prospectos asignados.",14);
            EditText name=field("Nombre",p.exists()?value(p,"name"):value(request,"name"),false,120);
            CheckBox active=check("Acceso aprobado",p.exists()&&Boolean.TRUE.equals(p.getBoolean("active")));
            CheckBox suspended=check("Suspender acceso",p.exists()&&Boolean.TRUE.equals(p.getBoolean("suspended")));
            CheckBox fe=check("Clientes Final Expense",p.exists()&&Boolean.TRUE.equals(p.get("scopes.clients")));
            CheckBox rec=check("Reclutamiento",p.exists()&&Boolean.TRUE.equals(p.get("scopes.recruitment")));
            Button save=button("Guardar autorización",()->{});
            save.setOnClickListener(v->{if(input(name).isEmpty()){message.setText("Escribe el nombre.");return;}
                Map<String,Object> d=new HashMap<>(),scopes=new HashMap<>();scopes.put("clients",fe.isChecked());scopes.put("recruitment",rec.isChecked());
                d.put("role","agent");d.put("email",request.getString("email"));d.put("name",input(name));d.put("active",active.isChecked());d.put("suspended",suspended.isChecked());d.put("scopes",scopes);
                save.setEnabled(false);store.save("users",request.getId(),d,AgentStore.revision(p)).addOnCompleteListener(activity,s->{if(!current(ticket))return;if(s.isSuccessful())accounts(null);else{save.setEnabled(true);error(s.getException());}});
            });
            if(p.exists())button("Dispositivos y avisos",()->devices(p.getId(),null));
            if(p.exists())button("Historial de permisos",()->history("users",p.getId(),"audit",null,()->account(request)));
        });
    }
    private void notificationSettings(){int ticket=screen("Avisos de asignación");back();
        DocumentReference ref=store.db.collection("users").document(uid).collection("preferences").document("operational");
        ref.get(Source.SERVER).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(!t.isSuccessful()){error(t.getException());return;}
            boolean enabled=!Boolean.FALSE.equals(t.getResult().getBoolean("notifications"));
            activity.getSharedPreferences("pag_native",0).edit().putBoolean("notifications",enabled).apply();
            CheckBox toggle=check("Recibir avisos de nuevas asignaciones",enabled);
            button("Guardar preferencia",()->{Map<String,Object>d=new HashMap<>();d.put("autoRefresh",true);d.put("notifications",toggle.isChecked());d.put("updatedAt",FieldValue.serverTimestamp());
                ref.set(d).addOnCompleteListener(activity,saved->{if(!current(ticket))return;if(saved.isSuccessful()){activity.getSharedPreferences("pag_native",0).edit().putBoolean("notifications",toggle.isChecked()).apply();message.setText("Preferencia guardada.");}else error(saved.getException());});
            });
            text("Los avisos requieren permiso de Android, el teléfono aprobado por Juan y el servicio de avisos activado.",14);
        });
    }
    private void devices(String agentUid,DocumentSnapshot cursor){int ticket=screen("Dispositivos del agente");back();
        text("Aprueba solo el teléfono que el agente te confirme. Una renovación del registro requiere aprobarlo nuevamente.",15);
        Query q=store.db.collection("users").document(agentUid).collection("deviceRequests").orderBy(FieldPath.documentId()).limit(20);if(cursor!=null)q=q.startAfter(cursor);
        q.get(Source.SERVER).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(!t.isSuccessful()){error(t.getException());return;}
            if(t.getResult().isEmpty())text("No hay dispositivos registrados. El agente debe abrir la app y permitir notificaciones.",16);
            for(DocumentSnapshot request:t.getResult()){
                String id=request.getId();String label="Teléfono …"+id.substring(Math.max(0,id.length()-4))+" · "+value(request,"appVersion");
                button(label+" · Revisar",()->{
                    store.db.collection("agentDevices").document(id).get(Source.SERVER).addOnCompleteListener(activity,read->{if(!current(ticket))return;if(!read.isSuccessful()){error(read.getException());return;}
                        DocumentSnapshot prior=read.getResult();String token=request.getString("fcmToken");if(token==null){message.setText("Registro incompleto.");return;}
                        String hash;try{StringBuilder hex=new StringBuilder();for(byte b:java.security.MessageDigest.getInstance("SHA-256").digest(token.getBytes(java.nio.charset.StandardCharsets.UTF_8)))hex.append(String.format(java.util.Locale.US,"%02x",b&255));hash=hex.toString();}catch(Exception e){error(e);return;}
                        boolean approved=prior.exists()&&Boolean.TRUE.equals(prior.getBoolean("enabled"))&&hash.equals(prior.getString("approvedTokenSha256"));
                        dialog=new AlertDialog.Builder(activity).setTitle(label).setMessage(approved?"Este registro está aprobado. Puedes suspender sus avisos.":"¿El agente confirmó este teléfono? Aprueba para permitir avisos genéricos, sin datos del prospecto.")
                            .setNegativeButton("Volver",null).setPositiveButton(approved?"Suspender avisos":"Aprobar teléfono",(x,w)->{
                                Map<String,Object>d=new HashMap<>();d.put("userId",agentUid);d.put("deviceId",id);d.put("enabled",!approved);d.put("approvedTokenSha256",hash);
                                store.save("agentDevices",id,d,AgentStore.revision(prior)).addOnCompleteListener(activity,saved->{if(!current(ticket))return;if(saved.isSuccessful())message.setText(approved?"Avisos suspendidos.":"Teléfono aprobado. Falta que el servicio de avisos esté activado para enviar.");else error(saved.getException());});
                            }).show();
                    });
                });
            }
            if(t.getResult().size()==20)button("Más dispositivos",()->devices(agentUid,t.getResult().getDocuments().get(19)));
        });
    }
    private void records(String bucket,DocumentSnapshot cursor){int ticket=screen(bucket.equals("clients")?"Clientes Final Expense":"Reclutamiento asignado");back();
        if(owner)button("Agregar prospecto",()->editContact(bucket,null,null));
        Query q=store.db.collection(bucket);if(!owner)q=q.whereEqualTo("assignedTo",uid);q=q.orderBy(FieldPath.documentId()).limit(50);if(cursor!=null)q=q.startAfter(cursor);
        LinearLayout rows=new LinearLayout(activity);rows.setOrientation(1);body.addView(rows);
        watches.add(q.addSnapshotListener(MetadataChanges.INCLUDE,(snap,e)->{if(!current(ticket))return;if(e!=null){rows.removeAllViews();error(e);return;}if(snap==null||snap.getMetadata().isFromCache()||snap.getMetadata().hasPendingWrites())return;
            rows.removeAllViews();message.setText(snap.isEmpty()?"No hay prospectos en esta página.":"Actualizado · "+snap.size()+" prospectos en esta página");
            for(DocumentSnapshot d:snap){Button row=new Button(activity);row.setAllCaps(false);String kind=bucket.equals("clients")?" · "+value(d,"classification")+" · "+value(d,"status"):"";row.setText(value(d,"name")+kind+"\n"+(value(d,"assignedTo").isEmpty()?"Sin asignar":"Asignado"));rows.addView(row);row.setOnClickListener(v->detail(bucket,d.getId()));}
            if(snap.size()==50){Button more=new Button(activity);more.setText("Siguiente página");rows.addView(more);more.setOnClickListener(v->records(bucket,snap.getDocuments().get(49)));}
        }));if(cursor!=null)button("Primera página",()->records(bucket,null));
    }
    private void watchAssignment(String bucket,String id,int ticket){
        watches.add(store.db.collection(bucket).document(id).addSnapshotListener(MetadataChanges.INCLUDE,(d,e)->{
            if(!current(ticket))return;
            if(e!=null||(d!=null&&!d.getMetadata().isFromCache()&&(!d.exists()||(!owner&&!uid.equals(d.getString("assignedTo")))))){
                records(bucket,null);message.setText("El acceso a este prospecto cambió. Se cerró su información.");
            }
        }));
    }
    private void detail(String bucket,String id){int ticket=screen("Prospecto");back();
        store.db.collection(bucket).document(id).get(Source.SERVER).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(!t.isSuccessful()){error(t.getException());return;}DocumentSnapshot d=t.getResult();if(!d.exists()){records(bucket,null);return;}
            watchAssignment(bucket,id,ticket);text(value(d,"name"),23);text(value(d,"phone")+"\n"+value(d,"email")+"\n"+value(d,"region"),16);
            String phone=value(d,"phone").replaceAll("[^0-9+]","");
            if(phone.matches("\\+?[0-9]{7,15}")){button("Llamar",()->open("tel:"+phone));button("Abrir WhatsApp",()->open("https://wa.me/"+phone.replace("+","")));}
            if(owner)button("Datos, clasificación y asignación",()->editContact(bucket,d,null));
            button("Historial de asignaciones y cambios",()->history(bucket,id,"audit",null,()->detail(bucket,id)));
            if(bucket.equals("clients")){operation(bucket,id,d,d,ticket);return;}
            store.db.collection("recruitmentState").document(id).get(Source.SERVER).addOnCompleteListener(activity,state->{if(!current(ticket))return;if(!state.isSuccessful()){error(state.getException());return;}operation(bucket,id,d,state.getResult(),ticket);});
        });
    }
    private void open(String uri){try{activity.startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(uri)));}catch(Exception e){message.setText("No hay una aplicación disponible para abrir este enlace.");}}
    private void operation(String bucket,String id,DocumentSnapshot contact,DocumentSnapshot state,int ticket){
        Spinner status=select("Estado",STATUSES,state.exists()?value(state,"status"):"Nuevo");EditText note=field("Nota interna",state.exists()?value(state,"note"):"",true,4000);
        Button save=button("Guardar seguimiento",()->{});
        save.setOnClickListener(v->{save.setEnabled(false);message.setText("Guardando…");
            if(bucket.equals("clients")){Map<String,Object> data=new HashMap<>(contact.getData());data.put("status",status.getSelectedItem().toString());data.put("note",input(note));store.save(bucket,id,data,AgentStore.revision(contact)).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(t.isSuccessful())detail(bucket,id);else{save.setEnabled(true);error(t.getException());}});}
            else try{
                String device=activity.getSharedPreferences("pag_native",0).getString("firebase_device_id","");if(device.length()<16){device=UUID.randomUUID().toString();activity.getSharedPreferences("pag_native",0).edit().putString("firebase_device_id",device).apply();}
                JSONObject input=new JSONObject().put("leadId",id).put("status",status.getSelectedItem().toString()).put("note",input(note)).put("baseRevision",AgentStore.revision(state)).put("eventId",UUID.randomUUID().toString());
                new RecruitmentSync(uid,device).save(input,(ok,response)->{if(!current(ticket))return;save.setEnabled(true);if(ok&&"saved".equals(response.optString("outcome")))detail(bucket,id);else message.setText(ok?"Hay cambios de otro teléfono. Conservamos tu edición en pantalla; vuelve a abrir el prospecto para revisar antes de guardar.":"No se guardó. Revisa tu acceso y conexión.");});
            }catch(Exception e){save.setEnabled(true);error(e);}
        });
        if(!bucket.equals("clients"))button("Historial de estados y notas",()->history("recruitmentState",id,"activity",null,()->detail(bucket,id)));
        button("Volver a la lista",()->records(bucket,null));
    }
    void importRecruitment(Map<String,Object> source,String id){int ticket=screen("Preparar reclutamiento para asignación");
        store.db.collection("recruitmentAssignments").document(id).get(Source.SERVER).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(!t.isSuccessful()){error(t.getException());return;}if(t.getResult().exists()){detail("recruitmentAssignments",id);return;}
            Map<String,Object> initial=new HashMap<>(source);initial.put("id",id);editContact("recruitmentAssignments",null,initial);
        });
    }
    private void editContact(String bucket,DocumentSnapshot existing,Map<String,Object> initial){int ticket=screen(existing==null?"Agregar prospecto":"Datos y asignación");back();
        Map<String,Object> base=existing!=null?existing.getData():initial!=null?initial:new HashMap<>();
        String id=existing!=null?existing.getId():initial!=null?(String)initial.get("id"):(bucket.equals("clients")?"c_":"r_")+UUID.randomUUID();
        EditText name=field("Nombre",Objects.toString(base.get("name"),""),false,200),phone=field("Teléfono con código de país",Objects.toString(base.get("phone"),""),false,40),email=field("Correo",Objects.toString(base.get("email"),""),false,254),region=field("Estado / región",Objects.toString(base.get("region"),""),false,120);
        Spinner classification=bucket.equals("clients")?select("Clasificación",new String[]{"LEAD","B_LEAD"},Objects.toString(base.get("classification"),"LEAD")):null;
        text("Asignar a",14);Spinner agents=new Spinner(activity);body.addView(agents);ArrayList<String>uids=new ArrayList<>(),names=new ArrayList<>();uids.add("");names.add("Sin asignar · inventario de Juan");
        String old=Objects.toString(base.get("assignedTo"),"");if(!old.isEmpty()){uids.add(old);names.add("Asignación actual · "+old);}
        agents.setAdapter(new ArrayAdapter<>(activity,android.R.layout.simple_spinner_dropdown_item,names));if(!old.isEmpty())agents.setSelection(1);
        String module=bucket.equals("clients")?"clients":"recruitment";
        Button save=button("Guardar prospecto y asignación",()->{});save.setEnabled(false);
        loadAssignees(module,null,uids,names,()->{if(!current(ticket))return;agents.setAdapter(new ArrayAdapter<>(activity,android.R.layout.simple_spinner_dropdown_item,names));agents.setSelection(Math.max(0,uids.indexOf(old)));save.setEnabled(true);},ticket);
        save.setOnClickListener(v->{if(input(name).isEmpty()){message.setText("Escribe un nombre.");return;}
            Map<String,Object>d=new HashMap<>();d.put("name",input(name));d.put("phone",input(phone));d.put("email",input(email));d.put("region",input(region));d.put("assignedTo",uids.get(agents.getSelectedItemPosition()));
            if(bucket.equals("clients")){d.put("classification",classification.getSelectedItem().toString());d.put("status",Objects.toString(base.get("status"),"Nuevo"));d.put("note",Objects.toString(base.get("note"),""));}
            String selected=names.get(agents.getSelectedItemPosition());
            dialog=new AlertDialog.Builder(activity).setTitle("Confirmar asignación").setMessage(input(name)+"\n"+selected+"\nEl agente elegido podrá ver el contacto, las notas y el historial de este prospecto.").setNegativeButton("Revisar",null).setPositiveButton("Guardar",(x,w)->{
                save.setEnabled(false);store.save(bucket,id,d,existing==null?0:AgentStore.revision(existing)).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(t.isSuccessful())detail(bucket,id);else{save.setEnabled(true);error(t.getException());}});
            }).show();
        });
        text("Los cambios conservan el historial. Al retirar o reasignar, el agente anterior pierde acceso a nuevas consultas.",14);
    }
    private void loadAssignees(String module,DocumentSnapshot cursor,ArrayList<String>uids,ArrayList<String>names,Runnable done,int ticket){
        Query q=store.db.collection("users").whereEqualTo("role","agent").orderBy(FieldPath.documentId()).limit(100);if(cursor!=null)q=q.startAfter(cursor);
        q.get(Source.SERVER).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(!t.isSuccessful()){error(t.getException());return;}
            for(DocumentSnapshot p:t.getResult())if(Boolean.TRUE.equals(p.getBoolean("active"))&&!Boolean.TRUE.equals(p.getBoolean("suspended"))&&Boolean.TRUE.equals(p.get("scopes."+module))){int i=uids.indexOf(p.getId());String label=value(p,"name")+" · "+value(p,"email");if(i>=0)names.set(i,label);else{uids.add(p.getId());names.add(label);}}
            if(t.getResult().size()==100)loadAssignees(module,t.getResult().getDocuments().get(99),uids,names,done,ticket);else done.run();
        });
    }
    private void history(String bucket,String id,String sub,DocumentSnapshot cursor,Runnable back){int ticket=screen("Historial");button("Volver al prospecto / agente",back);
        if(!owner)watchAssignment(bucket.equals("recruitmentState")?"recruitmentAssignments":bucket,id,ticket);
        Query q=store.db.collection(bucket).document(id).collection(sub).orderBy("createdAt",Query.Direction.DESCENDING).orderBy(FieldPath.documentId(),Query.Direction.DESCENDING).limit(30);if(cursor!=null)q=q.startAfter(cursor);
        q.get(Source.SERVER).addOnCompleteListener(activity,t->{if(!current(ticket))return;if(!t.isSuccessful()){error(t.getException());return;}if(t.getResult().isEmpty())text("Sin eventos en esta página.",16);
            for(DocumentSnapshot d:t.getResult()){Timestamp time=d.getTimestamp("createdAt");text((time==null?"":java.text.DateFormat.getDateTimeInstance().format(time.toDate()))+"\nAutor: "+value(d,"actorUid"),14);
                if(sub.equals("activity"))text("Estado: "+value(d,"previousStatus")+" → "+value(d,"status")+"\nNota: "+value(d,"note"),16);
                else {Map<String,Object>before=(Map<String,Object>)d.get("before"),after=(Map<String,Object>)d.get("after");StringBuilder changes=new StringBuilder();if(after!=null)for(String key:Arrays.asList("name","phone","email","region","classification","assignedTo","status","note","active","suspended","scopes")){Object was=before==null?null:before.get(key),now=after.get(key);if(!Objects.equals(was,now))changes.append(label(key)).append(": ").append(was==null?"—":was).append(" → ").append(now==null?"—":now).append("\n");}text(changes.toString(),16);}
            }
            if(t.getResult().size()==30)button("Ver anteriores",()->history(bucket,id,sub,t.getResult().getDocuments().get(29),back));
        });
    }
    private String label(String k){switch(k){case"assignedTo":return"Agente asignado";case"classification":return"Clasificación";case"status":return"Estado";case"note":return"Nota";case"active":return"Aprobado";case"suspended":return"Suspendido";case"scopes":return"Permisos";case"name":return"Nombre";case"phone":return"Teléfono";case"email":return"Correo";case"region":return"Región";default:return k;}}
}
