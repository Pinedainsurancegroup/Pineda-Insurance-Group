package com.pimflextv.next;
import android.content.Context;
import android.content.SharedPreferences;
import org.json.JSONArray;
import org.json.JSONObject;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import static org.junit.Assert.*;

@RunWith(RobolectricTestRunner.class)
@Config(manifest=Config.NONE, sdk=28)
public class PortableBackupStoreTest {
    private SharedPreferences prefs;
    private Context context;
    @Before public void setup() { context=RuntimeEnvironment.getApplication(); prefs=context.getSharedPreferences("backup-tests",0); prefs.edit().clear().commit(); }
    private JSONObject account(String user) throws Exception { return new JSONObject().put("id",PortableBackupData.accountId("https://example.invalid",user)).put("server","https://example.invalid").put("username",user).put("password",""); }
    private PortableBackupData.Parsed incoming(JSONArray accounts, Map<String,Object> values) throws Exception { return PortableBackupData.parse(PortableBackupData.create(values,accounts)); }
    @Test public void mergesFavoritesAndPreservesExistingSettingsAndSecrets() throws Exception {
        String id=account("existing").getString("id");
        prefs.edit().putString("saved_accounts",new JSONArray().put(account("existing")).toString())
                .putString("secure_secret_account_"+id+"_cipher","must-stay")
                .putInt("network_cache_ms",2500).putStringSet("favorites_aabb",new HashSet<>(Arrays.asList("live:1"))).commit();
        Map<String,Object> values=new HashMap<>(); values.put("network_cache_ms",5000); values.put("clone_clock_24",true);
        values.put("favorites_aabb",new HashSet<>(Arrays.asList("live:2")));
        int added=PortableBackupStore.restore(context,prefs,incoming(new JSONArray().put(account("existing")).put(account("new")),values));
        assertEquals(1,added); assertEquals(2,new JSONArray(prefs.getString("saved_accounts","[]")).length());
        assertEquals(2500,prefs.getInt("network_cache_ms",0)); assertTrue(prefs.getBoolean("clone_clock_24",false));
        assertEquals(2,prefs.getStringSet("favorites_aabb",new HashSet<>()).size());
        assertEquals("must-stay",prefs.getString("secure_secret_account_"+id+"_cipher",""));
    }
    @Test public void capacityFailureDoesNotPartiallyWrite() throws Exception {
        JSONArray old=new JSONArray(); for(int i=0;i<11;i++) old.put(account("old"+i));
        prefs.edit().putString("saved_accounts",old.toString()).putBoolean("clone_clock_24",false).commit();
        Map<String,?> before=new HashMap<>(prefs.getAll());
        PortableBackupData.Parsed data=incoming(new JSONArray().put(account("first")).put(account("second")),new HashMap<>());
        assertThrows(Exception.class,()->PortableBackupStore.restore(context,prefs,data)); assertEquals(before,prefs.getAll());
    }
    @Test public void collisionWithExistingAccountDoesNotOverwrite() throws Exception {
        prefs.edit().putString("saved_accounts",new JSONArray().put(account("Aa")).toString()).commit();
        Map<String,?> before=new HashMap<>(prefs.getAll());
        PortableBackupData.Parsed data=incoming(new JSONArray().put(account("BB")),new HashMap<>());
        assertThrows(Exception.class,()->PortableBackupStore.restore(context,prefs,data)); assertEquals(before,prefs.getAll());
    }
    @Test @Config(sdk=21) public void unsupportedKeystoreDoesNotPartiallyImport() throws Exception {
        PortableBackupData.Parsed data=incoming(new JSONArray().put(account("first")).put(account("secret").put("password","example")),new HashMap<>());
        assertThrows(Exception.class,()->PortableBackupStore.restore(context,prefs,data)); assertTrue(prefs.getAll().isEmpty());
    }
}
