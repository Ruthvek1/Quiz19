import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Users } from 'lucide-react'

function AdminUsers() {
  return (
    <div className="container mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="w-6 h-6 mr-2" />
            Manage Users
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p>User management interface will be implemented here.</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default AdminUsers

