import React from 'react'
import { useParams } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Trophy } from 'lucide-react'

function ResultPage() {
  const { sessionToken } = useParams()

  return (
    <div className="container mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Trophy className="w-6 h-6 mr-2" />
            Quiz Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p>Quiz results will be displayed here.</p>
          <p>Session Token: {sessionToken}</p>
        </CardContent>
      </Card>
    </div>
  )
}

export default ResultPage

