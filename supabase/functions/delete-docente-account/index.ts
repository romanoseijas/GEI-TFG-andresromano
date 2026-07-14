import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response(JSON.stringify({ error: 'No authorization header' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseAnonKey = Deno.env.get('SUPABASE_ANON_KEY')!
    const supabaseServiceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!

    const userClient = createClient(supabaseUrl, supabaseAnonKey, {
      global: { headers: { Authorization: authHeader } },
    })

    const { data: { user: caller } } = await userClient.auth.getUser()
    if (!caller) {
      return new Response(JSON.stringify({ error: 'Invalid token' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    // Check caller is ADMIN
    const { data: profile } = await userClient
      .from('profiles')
      .select('rol')
      .eq('id', caller.id)
      .single()

    if (profile?.rol !== 'ADMIN') {
      return new Response(JSON.stringify({ error: 'Only admins can delete accounts' }), {
        status: 403,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const { docente_id } = await req.json()
    if (!docente_id) {
      return new Response(JSON.stringify({ error: 'docente_id is required' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    const adminClient = createClient(supabaseUrl, supabaseServiceKey)

    // Get the docente to find user_id
    const { data: docente, error: fetchError } = await adminClient
      .from('docentes')
      .select('user_id')
      .eq('id', docente_id)
      .single()

    if (fetchError || !docente) {
      return new Response(JSON.stringify({ error: 'Docente not found' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    if (!docente.user_id) {
      return new Response(JSON.stringify({ error: 'Docente has no linked account' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    // Unlink the docente from the auth user
    const { error: unlinkError } = await adminClient
      .from('docentes')
      .update({ user_id: null })
      .eq('id', docente_id)

    if (unlinkError) {
      return new Response(JSON.stringify({ error: unlinkError.message }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    // Delete the auth user
    const { error: deleteError } = await adminClient.auth.admin.deleteUser(docente.user_id)

    if (deleteError) {
      // Rollback: re-link the user_id
      await adminClient
        .from('docentes')
        .update({ user_id: docente.user_id })
        .eq('id', docente_id)

      return new Response(JSON.stringify({ error: deleteError.message }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    return new Response(
      JSON.stringify({ success: true }),
      { status: 200, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
