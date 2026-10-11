package com.pimflextv.next;

import org.junit.Test;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import static org.junit.Assert.*;

public class PortableBackupTest {
    private final char[] password="Una frase única 2026!".toCharArray();
    private byte[] utf8(String s) { return s.getBytes(StandardCharsets.UTF_8); }
    @Test public void encryptedRoundTripAndRandomizedFiles() throws Exception {
        byte[] clear=utf8("https://example.invalid/list?username=demo&password=sensitive");
        byte[] a=PortableBackupCrypto.encrypt(clear,password), b=PortableBackupCrypto.encrypt(clear,password);
        assertFalse(Arrays.equals(a,b));
        assertArrayEquals(clear,PortableBackupCrypto.decrypt(a,password));
        assertFalse(new String(a,StandardCharsets.UTF_8).contains("sensitive"));
    }
    @Test public void wrongPasswordAndTamperingFailClosed() throws Exception {
        byte[] encrypted=PortableBackupCrypto.encrypt(utf8("credentials"),password);
        assertThrows(Exception.class,()->PortableBackupCrypto.decrypt(encrypted,"Wrong password 2026".toCharArray()));
        encrypted[encrypted.length-1]^=1;
        assertThrows(Exception.class,()->PortableBackupCrypto.decrypt(encrypted,password));
        byte[] changedHeader=PortableBackupCrypto.encrypt(utf8("credentials"),password);
        changedHeader[20]^=1;
        assertThrows(Exception.class,()->PortableBackupCrypto.decrypt(changedHeader,password));
    }
    @Test public void boundedInputsAndTruncationRejected() throws Exception {
        assertThrows(Exception.class,()->PortableBackupCrypto.readBounded(new ByteArrayInputStream(new byte[PortableBackupCrypto.MAX_FILE+1])));
        assertThrows(Exception.class,()->PortableBackupCrypto.encrypt(utf8("x"),"short".toCharArray()));
        byte[] encrypted=PortableBackupCrypto.encrypt(utf8("credentials"),password);
        assertThrows(Exception.class,()->PortableBackupCrypto.decrypt(Arrays.copyOf(encrypted,20),password));
        byte[] changedIterations=encrypted.clone(); changedIterations[14]=0x7f;
        assertThrows(Exception.class,()->PortableBackupCrypto.decrypt(changedIterations,password));
    }
    @Test public void typesAndSourceUrlsSurviveButDeviceSecretsDoNot() throws Exception {
        Map<String,Object> prefs=new HashMap<>();
        prefs.put("network_cache_ms",2500); prefs.put("clone_clock_24",true);
        prefs.put("m3u_url","https://example.invalid/get?password=private");
        prefs.put("favorites_aabb",new HashSet<>(Arrays.asList("live:10","vod:12")));
        prefs.put("secure_secret_account_1_cipher","device-bound"); prefs.put("opensubtitles_api_key","secret");
        prefs.put("ovpn_uri","content://device/private"); prefs.put("parental_enabled_aabb",false);
        PortableBackupData.Parsed p=PortableBackupData.parse(PortableBackupData.create(prefs,new JSONArray()));
        assertEquals(4,p.prefs.size()); assertTrue(p.prefs.get("network_cache_ms") instanceof Integer);
        assertEquals(prefs.get("favorites_aabb"),p.prefs.get("favorites_aabb"));
        assertEquals(prefs.get("m3u_url"),p.prefs.get("m3u_url"));
    }
    @Test public void unsafeUnknownKeysIgnoredAndKnownBadTypesRejected() throws Exception {
        JSONObject legacy=new JSONObject().put("format","PIMFLEX_BACKUP_1").put("prefs",new JSONObject()
                .put("remember",true).put("secure_password","attacker").put("network_cache_ms","wrong"));
        assertThrows(Exception.class,()->PortableBackupData.parse(legacy));
        legacy.getJSONObject("prefs").put("network_cache_ms",5000L);
        PortableBackupData.Parsed p=PortableBackupData.parse(legacy);
        assertEquals(1,p.prefs.size()); assertEquals(5000,p.prefs.get("network_cache_ms")); assertTrue(p.legacy);
    }
    @Test public void legacyAccountsRequirePasswordAgain() throws Exception {
        JSONObject account=new JSONObject().put("id","untrusted").put("server","https://example.invalid").put("username","demo").put("password","not-trusted");
        JSONObject legacy=new JSONObject().put("format","PIMFLEX_BACKUP_1").put("prefs",new JSONObject().put("saved_accounts",new JSONArray().put(account).toString()));
        PortableBackupData.Parsed p=PortableBackupData.parse(legacy);
        assertEquals("",p.accounts.getJSONObject(0).getString("password"));
        assertEquals(PortableBackupData.accountId("https://example.invalid","demo"),p.accounts.getJSONObject(0).getString("id"));
    }
    @Test public void collisionsAndNonHttpServersRejected() throws Exception {
        JSONArray accounts=new JSONArray();
        for(String user:new String[]{"Aa","BB"}) accounts.put(new JSONObject().put("server","https://example.invalid").put("username",user).put("password",""));
        JSONObject payload=PortableBackupData.create(new HashMap<>(),accounts);
        assertThrows(Exception.class,()->PortableBackupData.parse(payload));
        payload.put("accounts",new JSONArray().put(new JSONObject().put("server","file:///etc/private").put("username","demo").put("password","")));
        assertThrows(Exception.class,()->PortableBackupData.parse(payload));
    }
    @Test public void oversizedNestingRejectedBeforeParser() {
        String text="{\"x\":" + String.join("",java.util.Collections.nCopies(1000,"["));
        assertThrows(Exception.class,()->PortableBackupData.readJson(text));
    }
}
